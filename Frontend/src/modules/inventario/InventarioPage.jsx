
import React, { useRef, useState } from 'react';
import { readSession } from '../../api.js';
import CategoryFilter from './CategoryFilter.jsx';
import DropdownSelect from '../../components/DropdownSelect.jsx';
import {
  money,
  find,
  Field,
  PageHeading,
  Modal,
  Input,
  Table,
} from '../../components/AdminCatalogShared.jsx';

const emptyProduct = {
  codigo: '',
  nombre: '',
  descripcion: '',
  categoria_id: '',
  proveedor_id: '',
  unidad_medida: 'unidad',
  precio_compra: 0,
  precio_venta: 0,
  existencia: 0,
  stock_minimo: 0,
  imagen_url: '',
  activo: true,
};

export default function InventarioPage({ data, mutate }) {
  const products = data.productos || [];
  const categories = data.categorias || [];
  const suppliers = data.proveedores || [];
  const moves = data.movimientos || [];

  const [query, setQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [form, setForm] = useState(null);
  const [movement, setMovement] = useState(null);
  const [error, setError] = useState('');
  const [removalError, setRemovalError] = useState('');
  const [removingProduct, setRemovingProduct] = useState(null);
  const [showMoves, setShowMoves] = useState(false);
  const lowStockCount = products.filter(p => Number(p.existencia) <= Number(p.stock_minimo)).length;

  // Cloudinary
  const archivoImagenRef = useRef(null);
  const [subiendoImagen, setSubiendoImagen] = useState(false);

  const filtered = products.filter(p => {
    const categoryName = find(categories, p.categoria_id)?.nombre || '';
    const matchesText = `${p.codigo} ${p.nombre} ${categoryName}`.toLowerCase().includes(query.trim().toLowerCase());
    const matchesCategory = !categoryFilter || String(p.categoria_id) === String(categoryFilter);
    const matchesStock = !showLowStockOnly || Number(p.existencia) <= Number(p.stock_minimo);
    return matchesText && matchesCategory && matchesStock;
  });

  // Subir imagen a Cloudinary
  async function subirImagen(event) {
    const input = event.currentTarget;
    const archivo = input.files?.[0];

    if (!archivo) return;

    setError('');

    const formatosPermitidos = [
      'image/jpeg',
      'image/png',
      'image/webp',
    ];

    if (
      !formatosPermitidos.includes(archivo.type) ||
      archivo.size > 5 * 1024 * 1024
    ) {
      setError(
        'Seleccioná una imagen JPG, PNG o WebP de máximo 5 MB.'
      );
      input.value = '';
      return;
    }

    setSubiendoImagen(true);

    try {
      const token = readSession()?.token;

      if (!token) {
        throw new Error('Iniciá sesión nuevamente.');
      }

      const datos = new FormData();
      datos.append('imagen', archivo);

      const respuesta = await fetch(
        '/api/admin/productos/imagen/',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: datos,
        }
      );

      const resultado = await respuesta
        .json()
        .catch(() => ({}));

      if (!respuesta.ok || !resultado.imagen_url) {
        throw new Error(
          typeof resultado.error === 'string'
            ? resultado.error
            : 'No se pudo subir la imagen a Cloudinary.'
        );
      }

      // Guardar la URL en el formulario del producto
      setForm(actual =>
        actual
          ? {
              ...actual,
              imagen_url: resultado.imagen_url,
            }
          : actual
      );

    } catch (err) {
      setError(err.message || 'Error al subir la imagen.');
    } finally {
      setSubiendoImagen(false);
      input.value = '';
    }
  }

  // Guardar o editar un producto
  async function saveProduct(e) {
    e.preventDefault();
    setError('');

    if (subiendoImagen) {
      return setError(
        'Esperá a que termine de subir la imagen.'
      );
    }

    if (
      !form.nombre.trim() ||
      !form.unidad_medida.trim() ||
      !form.categoria_id
    ) {
      return setError(
        'Seleccioná una categoría y completá el nombre y la unidad de medida.'
      );
    }

    if (
      ['precio_compra', 'precio_venta', 'stock_minimo'].some(
        k =>
          form[k] === '' ||
          !Number.isFinite(Number(form[k])) ||
          Number(form[k]) < 0
      )
    ) {
      return setError(
        'Los precios y las existencias deben ser números iguales o mayores que cero.'
      );
    }

    const { id } = form;

    // Enviar únicamente los campos aceptados por la API
    const product = Object.fromEntries(
      Object.keys(emptyProduct)
        .filter(key => key !== 'existencia')
        .map(key => [key, form[key]])
    );

    try {
      await mutate(
        '/admin/productos' + (id ? '/' + id : ''),
        {
          ...product,
          codigo: id ? product.codigo : undefined,
          categoria_id: product.categoria_id,
          proveedor_id: product.proveedor_id || null,
          imagen_url: product.imagen_url || null,
          activo: Boolean(product.activo),
        },
        id ? 'PATCH' : 'POST'
      );

      setForm(null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeProduct(product) {
    if (!window.confirm(`¿Eliminar ${product.nombre} del catálogo? El producto se desactivará y conservará su historial.`)) return;
    setRemovingProduct(product.id);
    setRemovalError('');
    try {
      await mutate(`/admin/productos/${product.id}`, undefined, 'DELETE');
      if (String(form?.id) === String(product.id)) setForm(null);
    } catch (err) {
      setRemovalError(err.message || 'No se pudo eliminar el producto.');
    } finally {
      setRemovingProduct(null);
    }
  }

  // Registrar movimientos de inventario
  async function saveMovement(e) {
    e.preventDefault();

    const product = find(products, movement.producto_id);
    const qty = Number(movement.cantidad);

    if (
      !product ||
      movement.cantidad === '' ||
      !Number.isFinite(qty) ||
      (movement.tipo === 'AJUSTE' ? qty < 0 : qty <= 0)
    ) {
      return setError(
        'Seleccioná un producto y una cantidad válida.'
      );
    }

    const previous = Number(product.existencia);

    const current =
      movement.tipo === 'ENTRADA'
        ? previous + qty
        : movement.tipo === 'SALIDA'
          ? previous - qty
          : qty;

    if (current < 0) {
      return setError(
        'La salida no puede superar la existencia disponible.'
      );
    }

    if (
      movement.tipo === 'AJUSTE' &&
      current === previous
    ) {
      return setError(
        'La nueva existencia debe ser diferente de la actual.'
      );
    }

    try {
      await mutate('/inventario/movimientos', movement);
      setMovement(null);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHeading
        title="Inventario"
        description="Productos, existencias y movimientos de inventario."
        action="Agregar producto"
        onAction={() => {
          setError('');
          setForm({ ...emptyProduct });
        }}
      />

      <div className="ac-toolbar">
        <button
          type="button"
          className="ac-secondary"
          onClick={() => {
            setError('');
            setMovement({
              producto_id: '',
              tipo: 'ENTRADA',
              cantidad: '',
              motivo: '',
            });
          }}
        >
          Ajustar existencias
        </button>

        <button
          type="button"
          className="ac-secondary"
          onClick={() => setShowMoves(!showMoves)}
        >
          {showMoves ? 'Ver productos' : 'Ver movimientos'}
        </button>

        <span>{lowStockCount} productos con existencias bajas</span>
      </div>

      {!showMoves ? (
        <>
          {removalError && <p className="ac-error" role="alert">{removalError}</p>}
          <div className="module-summary inventory-filter-bar">
            <div className="search-box">
              <input type="search" aria-label="Buscar producto por nombre o código" placeholder="Buscar por nombre o código"
                value={query} onChange={event => setQuery(event.target.value)} />
            </div>
            <CategoryFilter categories={categories} value={categoryFilter} onChange={setCategoryFilter} />
            <button type="button" className={`inventory-low-stock-filter${showLowStockOnly ? ' is-active' : ''}`} aria-pressed={showLowStockOnly} onClick={() => setShowLowStockOnly(current => !current)}>
              <span className="inventory-low-stock-dot" aria-hidden="true" />
              <span>Stock bajo</span>
              <span className="inventory-low-stock-count">{lowStockCount}</span>
            </button>
          </div>

          <Table
            headers={[
              'Código',
              'Producto',
              'Categoría',
              'Precio venta',
              'Existencia',
              'Estado',
              'Acciones',
            ]}
            empty={!filtered.length}
          >
            {filtered.map(p => (
              <tr key={p.id}>
                <td>{p.codigo}</td>

                <td>{p.nombre}</td>

                <td>
                  {find(categories, p.categoria_id)?.nombre ||
                    'Sin categoría'}
                </td>

                <td>{money(p.precio_venta)}</td>

                <td>
                  {p.existencia} {p.unidad_medida}
                </td>

                <td>
                  <span
                    className={
                      p.activo
                        ? 'status'
                        : 'status status--no-disponible'
                    }
                  >
                    {!p.activo
                      ? 'No disponible'
                      : Number(p.existencia) <= 0
                        ? 'Agotado'
                        : Number(p.existencia) <=
                            Number(p.stock_minimo)
                          ? 'Stock bajo'
                          : 'Disponible'}
                  </span>
                </td>

                <td>
                  <button
                    type="button"
                    className="table-action"
                    onClick={() => {
                      setError('');
                      setForm({
                        ...emptyProduct,
                        ...p,
                      });
                    }}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    className="table-action table-action--danger"
                    disabled={removingProduct !== null}
                    onClick={() => removeProduct(p)}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        </>
      ) : (
        <Table
          headers={[
            'Fecha',
            'Producto',
            'Tipo',
            'Cantidad',
            'Antes',
            'Después',
            'Motivo',
          ]}
          empty={!moves.length}
        >
          {moves.map(m => (
            <tr key={m.id}>
              <td>
                {m.fecha
                  ? new Date(m.fecha).toLocaleString('es-CR')
                  : '—'}
              </td>

              <td>
                {find(products, m.producto_id)?.nombre ||
                  'Producto'}
              </td>

              <td>{m.tipo}</td>
              <td>{m.cantidad}</td>
              <td>{m.existencia_anterior}</td>
              <td>{m.existencia_nueva}</td>
              <td>{m.motivo || '—'}</td>
            </tr>
          ))}
        </Table>
      )}

      {/* Formulario para agregar o editar productos */}
      {form && (
        <Modal
          title={form.id ? 'Editar producto' : 'Agregar producto'}
          className="ac-modal--product"
          onClose={() => {
            if (!subiendoImagen) setForm(null);
          }}
        >
          <form onSubmit={saveProduct} className="ac-form">
            <div className="ac-grid">

              <Field label="Categoría *">
                <DropdownSelect
                  required
                  value={form.categoria_id || ''}
                  onChange={e =>
                    setForm({
                      ...form,
                      categoria_id: e.target.value,
                    })
                  }
                >
                  <option value="">Sin categoría</option>

                  {categories.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </DropdownSelect>
              </Field>

              <Field label="Nombre *">
                <Input
                  form={form}
                  setForm={setForm}
                  name="nombre"
                  maxLength="180"
                  required
                />
              </Field>

              <Field label="Proveedor">
                <DropdownSelect
                  value={form.proveedor_id || ''}
                  onChange={e =>
                    setForm({
                      ...form,
                      proveedor_id: e.target.value,
                    })
                  }
                >
                  <option value="">Sin proveedor</option>

                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.nombre}
                    </option>
                  ))}
                </DropdownSelect>
              </Field>

              <Field label="Unidad de medida *">
                <Input
                  form={form}
                  setForm={setForm}
                  name="unidad_medida"
                  maxLength="30"
                  required
                />
              </Field>

              <Field label="Precio de compra">
                <Input
                  form={form}
                  setForm={setForm}
                  name="precio_compra"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                />
              </Field>

              <Field label="Precio de venta">
                <Input
                  form={form}
                  setForm={setForm}
                  name="precio_venta"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                />
              </Field>

              <Field label="Stock mínimo">
                <Input
                  form={form}
                  setForm={setForm}
                  name="stock_minimo"
                  type="number"
                  min="0"
                  step="0.001"
                  required
                />
              </Field>

              {/* CLOUDINARY: Único botón para subir imagen */}
              <div className="ac-field">
                <span>Imagen del producto</span>

                <input
                  ref={archivoImagenRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={subirImagen}
                  style={{ display: 'none' }}
                />

                <div className="ac-product-image-control">
                  {form.imagen_url && <img className="ac-preview" src={form.imagen_url} alt="Vista previa del producto" />}
                  <button
                    type="button"
                    className="ac-secondary"
                    onClick={() => archivoImagenRef.current?.click()}
                    disabled={subiendoImagen}
                  >
                    {subiendoImagen ? 'Subiendo imagen...' : form.imagen_url ? 'Cambiar imagen' : 'Subir imagen'}
                  </button>
                </div>
              </div>

              <label className="ac-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(form.activo)}
                  onChange={e =>
                    setForm({
                      ...form,
                      activo: e.target.checked,
                    })
                  }
                />
                Producto disponible
              </label>

              <div className="ac-wide">
                <Field label="Descripción">
                  <textarea
                    value={form.descripcion || ''}
                    onChange={e =>
                      setForm({
                        ...form,
                        descripcion: e.target.value,
                      })
                    }
                    rows="2"
                  />
                </Field>
              </div>
            </div>

            {error && (
              <p className="ac-error" role="alert">
                {error}
              </p>
            )}

            <div className="ac-actions">
              <button
                type="button"
                className="ac-secondary"
                onClick={() => setForm(null)}
                disabled={subiendoImagen}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="primary-action"
                disabled={subiendoImagen}
              >
                {subiendoImagen
                  ? 'Subiendo imagen...'
                  : 'Guardar producto'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Formulario para movimientos de inventario */}
      {movement && (
        <Modal
          title="Ajuste manual de inventario"
          onClose={() => setMovement(null)}
        >
          <p className="inventory-movement-note">Usá este formulario para mermas, daños, correcciones o ingresos manuales. Las ventas descuentan existencias automáticamente y las compras las aumentan al marcarlas como recibidas.</p>
          <form className="ac-form" onSubmit={saveMovement}>
            <div className="ac-grid">

              <Field label="Producto *">
                <DropdownSelect
                  required
                  value={movement.producto_id}
                  onChange={e =>
                    setMovement({
                      ...movement,
                      producto_id: e.target.value,
                    })
                  }
                >
                  <option value="">
                    Seleccioná un producto
                  </option>

                  {products.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} ({p.existencia}{' '}
                      {p.unidad_medida})
                    </option>
                  ))}
                </DropdownSelect>
              </Field>

              <Field label="Tipo">
                <DropdownSelect
                  value={movement.tipo}
                  onChange={e =>
                    setMovement({
                      ...movement,
                      tipo: e.target.value,
                    })
                  }
                >
                  <option value="ENTRADA">
                    Entrada manual
                  </option>
                  <option value="SALIDA">
                    Salida manual
                  </option>
                  <option value="AJUSTE">
                    Fijar existencia
                  </option>
                </DropdownSelect>
              </Field>

              <Field
                label={
                  movement.tipo === 'AJUSTE'
                    ? 'Nueva existencia *'
                    : 'Cantidad *'
                }
              >
                <Input
                  form={movement}
                  setForm={setMovement}
                  name="cantidad"
                  type="number"
                  min={
                    movement.tipo === 'AJUSTE'
                      ? '0'
                      : '0.001'
                  }
                  step="0.001"
                  required
                />
              </Field>

              <Field label="Motivo del ajuste *">
                <Input
                  form={movement}
                  setForm={setMovement}
                  name="motivo"
                  maxLength="255"
                  required
                />
              </Field>

            </div>

            {error && (
              <p role="alert" className="ac-error">
                {error}
              </p>
            )}

            <div className="ac-actions">
              <button
                type="button"
                className="ac-secondary"
                onClick={() => setMovement(null)}
              >
                Cancelar
              </button>

              <button className="primary-action">
                Guardar movimiento
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
