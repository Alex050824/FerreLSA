
import React, { useEffect, useRef, useState } from 'react';
import { api } from '../../../api.js';
import { money } from '../utils.js';

async function cargarPayPal() {
  if (window.paypal?.createInstance) return;

  let script = document.querySelector(
    'script[data-ferrelsa-paypal]'
  );

  return new Promise((resolve, reject) => {
    if (script) {
      script.addEventListener('load', resolve, { once: true });
      script.addEventListener('error', reject, { once: true });
      return;
    }

    script = document.createElement('script');
    script.dataset.ferrelsaPaypal = '1';
    script.src =
      'https://www.sandbox.paypal.com/web-sdk/v6/core';
    script.async = true;
    script.onload = resolve;
    script.onerror = () =>
      reject(new Error('No se pudo cargar PayPal.'));

    document.head.appendChild(script);
  });
}

export default function Checkout({
  navigate,
  cart,
  cartLines,
  token,
  setCart,
  subtotal,
  onPaid,
}) {
  const [venta, setVenta] = useState(null);
  const [orden, setOrden] = useState(null);
  const [preparando, setPreparando] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');

  const ventaRef = useRef(null);
  const ocupadoRef = useRef(false);
  const contenedorRef = useRef(null);
  const callbacksRef = useRef(null);

  callbacksRef.current = { navigate, setCart, onPaid };

  const clientId = import.meta.env.VITE_PAYPAL_CLIENT_ID;

  async function prepararPago() {
    if (ocupadoRef.current || !token || !cart.length) return;

    ocupadoRef.current = true;
    setPreparando(true);
    setError('');
    setMensaje('');

    try {
      let ventaActual = ventaRef.current;

      if (!ventaActual) {
        ventaActual = await api('/ventas', {
          method: 'POST',
          token,
          body: {
            numero: `WEB-${Date.now()}`,
            canal: 'EN_LINEA',
            metodo_pago: 'PAYPAL',
            modalidad_entrega: 'RETIRO_TIENDA',
            detalles: cart.map(linea => ({
              producto_id: linea.productId,
              cantidad: Number(linea.quantity),
            })),
          },
        });

        ventaRef.current = ventaActual;
        setVenta(ventaActual);
      }

      const nuevaOrden = await api(
        `/ventas/${ventaActual.id}/paypal/crear`,
        { method: 'POST', token }
      );

      setOrden(nuevaOrden);
      setMensaje('Revisá el importe y continuá con PayPal.');
    } catch (err) {
      setError(err.message);
    } finally {
      ocupadoRef.current = false;
      setPreparando(false);
    }
  }

  useEffect(() => {
    if (!orden?.orden_id || !venta?.id || !token) return;

    let activo = true;
    let boton = null;
    let manejarClick = null;

    async function iniciarPayPal() {
      await cargarPayPal();

      const sdk = await window.paypal.createInstance({
        clientId,
        components: ['paypal-payments'],
        pageType: 'checkout',
      });

      const elegibilidad = await sdk.findEligibleMethods({
        currencyCode: 'USD',
      });

      if (!elegibilidad.isEligible('paypal')) {
        throw new Error(
          'PayPal no está disponible para esta cuenta.'
        );
      }

      const sesion = await sdk.createPayPalOneTimePaymentSession({
        onApprove: async () => {
          setProcesando(true);
          setError('');

          try {
            const resultado = await api(
              `/ventas/${venta.id}/paypal/capturar`,
              { method: 'POST', token }
            );

            if (resultado.estado !== 'PAGADA') {
              throw new Error(
                'El cobro todavía no está confirmado.'
              );
            }

            callbacksRef.current.setCart([]);
            callbacksRef.current.onPaid?.();
            callbacksRef.current.navigate('historial');
          } catch (err) {
            setError(
              `${err.message} No iniciés otra compra hasta revisar el estado de este pago.`
            );
          } finally {
            setProcesando(false);
          }
        },

        onCancel: () => {
          setMensaje(
            'No completaste la aprobación. La venta permanece pendiente.'
          );
        },

        onError: () => {
          setError(
            'PayPal reportó un problema. Revisá el estado del pedido antes de volver a intentar.'
          );
        },
      });

      if (!activo || !contenedorRef.current) return;

      boton = document.createElement('paypal-button');
      contenedorRef.current.replaceChildren(boton);

      manejarClick = () => {
        const promesaOrden = Promise.resolve({
          orderId: orden.orden_id,
        });

        sesion.start(
          { presentationMode: 'auto' },
          promesaOrden
        ).catch(err => {
          setError(err.message || 'No se pudo abrir PayPal.');
        });
      };

      boton.addEventListener('click', manejarClick);
    }

    iniciarPayPal().catch(err => {
      if (activo) {
        setError(err.message || 'Error al iniciar PayPal.');
      }
    });

    return () => {
      activo = false;

      if (boton && manejarClick) {
        boton.removeEventListener('click', manejarClick);
      }

      contenedorRef.current?.replaceChildren();
    };
  }, [orden?.orden_id, venta?.id, token, clientId]);


  async function cancelarPedido() {
    if (!ventaRef.current || procesando || ocupadoRef.current) {
      return;
    }

    ocupadoRef.current = true;
    setPreparando(true);
    setError('');

    try {
      await api(
        `/ventas/${ventaRef.current.id}/paypal/cancelar`,
        { method: 'POST', token }
      );

      ventaRef.current = null;
      setVenta(null);
      setOrden(null);

      setMensaje(
        'Pedido cancelado. Los productos siguen en tu carrito.'
      );
    } catch (err) {
      setError(err.message);
    } finally {
      ocupadoRef.current = false;
      setPreparando(false);
    }
  }

  return (
    <>
      <button
        className="store-link"
        onClick={() => navigate('carrito')}
        disabled={procesando}
      >
        ← Volver al carrito
      </button>

      <div className="store-page-heading">
        <h1>Finalizar pedido</h1>
        <p>Pago seguro con PayPal Sandbox.</p>
      </div>

      {!cart.length ? (
        <p className="store-empty">Tu carrito está vacío.</p>
      ) : (
        <div className="store-checkout-layout">
          <div className="store-cart-list">
            {cartLines.map(linea => (
              <article
                className="store-cart-line"
                key={linea.productId}
              >
                <div>
                  <strong>{linea.product?.nombre}</strong>
                  <small>
                    Cantidad: {linea.quantity}
                  </small>
                </div>

                <strong>
                  {money(
                    Number(linea.product?.precio_venta || 0) *
                    Number(linea.quantity)
                  )}
                </strong>
              </article>
            ))}
          </div>

          <aside className="store-summary">
            <h2>Resumen del pedido</h2>

            <div>
              <span>Subtotal estimado</span>
              <strong>{money(subtotal)}</strong>
            </div>

            <p>
              Los impuestos y el total definitivo se
              calculan en el servidor.
            </p>

            <p>Modalidad: Retiro en tienda.</p>

            {!orden && (
              <button
                className="store-button"
                onClick={prepararPago}
                disabled={
                  preparando ||
                  !token ||
                  !clientId ||
                  !cart.length
                }
              >
                {preparando
                  ? 'Preparando pago...'
                  : 'Preparar pago con PayPal'}
              </button>
            )}

            {orden && (
              <>
                <h3>Total de la compra</h3>

                <p>
                  Total en colones:
                  <strong> {money(orden.total_crc)}</strong>
                </p>

                <p>
                  Total en dólares:
                  <strong> USD {orden.total_usd}</strong>
                </p>

                <p>
                  Tipo de cambio:
                  ₡{orden.tipo_cambio} por USD
                </p>

                <p>Confirmá el importe antes de pagar.</p>

                <div ref={contenedorRef} />

                {procesando && (
                  <p role="status">
                    Verificando el cobro con PayPal...
                  </p>
                )}
              </>
            )}


            {venta && (
              <button
                type="button"
                className="store-link"
                onClick={cancelarPedido}
                disabled={preparando || procesando}
              >
                Cancelar pedido
              </button>
            )}

            {!token && (
              <p>Iniciá sesión para realizar la compra.</p>
            )}

            {!clientId && (
              <p>
                Falta configurar el Client ID de PayPal.
              </p>
            )}

            {mensaje && <p role="status">{mensaje}</p>}

            {error && <p role="alert">{error}</p>}
          </aside>
        </div>
      )}
    </>
  );
}
