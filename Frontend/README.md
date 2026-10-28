# Landing page FerreLSA (React)

Sitio web público, responsivo y de una sola página para presentar a la ferretería FerreLSA. Construido con **React + Vite + CSS**; no necesita Tailwind, Bootstrap ni librerías de iconos.

## Requisitos

- Node.js 20 o superior
- npm

## Ejecutar en desarrollo

```bash
npm install
npm run dev
```

Abrí en el navegador la dirección que muestre Vite, normalmente `http://localhost:5173/`.

## Preparar para producción

```bash
npm run build
npm run preview
```

Los archivos finales estarán en `dist/`.

## Archivos principales

- `src/App.jsx`: secciones y navegación de la landing.
- `src/components/Icons.jsx`: iconos SVG en React.
- `src/styles.css`: diseño y adaptación a dispositivos móviles.
- `public/assets/logo-ferrelsa.png`: logo tomado del proyecto original.
- `public/assets/emblema-ferrelsa.png`: recorte del emblema para la cabecera y favicon.

## Contenido y alcance

La información general de FerreLSA, la descripción de clientes y las categorías de productos se basan en el **anteproyecto Sistema ERP - FerreLSA**. Las secciones de **misión y visión son propuestas redactadas para esta landing**, ya que el documento no contiene textos oficiales sobre ellas. La sección de tecnología menciona el ERP como **propuesta en desarrollo**, no como un sistema ya implementado.

La landing **no vende en línea, no consulta inventario real y no se conecta al ERP**. Es una pantalla institucional/pública separada de los módulos privados. Se puede integrar luego dentro del repositorio del proyecto y conectar acciones reales cuando esos servicios estén listos.

## Integración en una aplicación React que ya existe

Si el proyecto ERP ya tiene su propio frontend React, no es obligatorio crear otra aplicación:

1. Copiá `src/App.jsx`, `src/components/Icons.jsx` y `src/styles.css` a las rutas equivalentes de tu frontend.
2. Copiá el contenido de `public/assets/` a la carpeta pública `assets/` del proyecto.
3. Importá el componente `App` como página principal o extraé las secciones que necesités para tu enrutador.
4. Conservá los estilos o adaptalos al diseño que ya tengan. No se necesita ninguna dependencia de UI adicional.

> La navegación usa enlaces internos (`#inicio`, `#nosotros`, etc.). No hay rutas al ERP porque el documento no especifica una ruta real de acceso.
