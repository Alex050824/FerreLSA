# FerreLSA ERP — Pantalla de acceso (React + Vite)

Nueva versión de la landing de FerreLSA: una **pantalla de inicio de sesión** para el sistema ERP, acompañada por misión, visión y una **vista ilustrativa** de sus módulos. Está basada en el anteproyecto académico de FerreLSA.

## Cómo ejecutarlo

1. Abrí `Frontend` en Visual Studio Code.
2. En PowerShell ejecutá:

   ```powershell
   npm.cmd install
   npm.cmd run dev
   ```

   Si `npm` funciona normalmente en tu equipo, podés usar `npm` en lugar de `npm.cmd`.

3. Abrí la URL local que indique Vite (generalmente `http://localhost:5173/`).

## Integración con el backend

El formulario valida que haya usuario y contraseña, permite mostrar/ocultar la contraseña, y ya contiene el punto de integración con el backend. **No autentica usuarios hasta configurar el endpoint real.** No usa usuarios de ejemplo ni simula una sesión válida.

1. Copiá `.env.example` como `.env` dentro de `Frontend/`.
2. Configurá `VITE_LOGIN_ENDPOINT` con el endpoint **real** del backend (ejemplo ilustrativo: `http://localhost:3000/api/auth/login`).
3. Revisá `src/services/auth.js`. Actualmente envía un POST JSON con el siguiente formato:

   ```json
   { "username": "usuario", "password": "contraseña" }
   ```

   Adaptá los nombres de los campos y la respuesta al contrato real de tu backend. Si está en otro puerto, configurá CORS y cookies correctamente en el servidor.
4. Cuando exista el panel administrativo, configurá `VITE_AFTER_LOGIN_PATH` con una ruta relativa que **exista** (por ejemplo, `/dashboard`).
5. En producción usá HTTPS. La gestión de la sesión y los permisos por rol debe implementarse y validarse en el backend. Evitá guardar contraseñas o tokens sensibles en `localStorage`.

⚠️ Las variables `VITE_*` son públicas en el navegador. **Nunca coloqués secretos, claves privadas ni contraseñas en estas variables.**

## Estructura

```text
Frontend/
├── public/assets/
│   ├── emblema-ferrelsa.png
│   └── logo-ferrelsa.png
├── src/
│   ├── components/Icon.jsx
│   ├── services/auth.js
│   ├── App.jsx
│   ├── main.jsx
│   └── styles.css
├── .env.example
├── .gitignore
├── index.html
├── package.json
└── vite.config.js
```

## Notas de contenido

- Las secciones y los módulos se fundamentan en el anteproyecto: Ventas, Inventario, Compras, Facturación, Clientes, Proveedores y Administración General.
- El recuadro de módulos es una **ilustración**, no un panel con datos reales.
- La misión y la visión son **redacciones propuestas**, pues el documento no incluye una misión y una visión oficiales.
- La carpeta `Backend` del repositorio no necesita reemplazarse. Los archivos de este ZIP pertenecen solo al frontend.

## Subir los cambios a GitHub

Desde la carpeta raíz `Proyecto` (donde ya inicializaste Git), después de verificar los cambios:

```powershell
git status
git add Frontend/
git commit -m "Rediseñar acceso ERP de FerreLSA"
git push
```

Si tu carpeta está nombrada `frontend` en minúsculas, usá ese nombre en `git add`.
