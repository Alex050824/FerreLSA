import React, { useState } from 'react';

export default function ProductImage({ product }) {
  const [broken, setBroken] = useState(false);
  return <div className="store-image">
    {product.imagen_url && !broken
      ? <img src={product.imagen_url} alt={product.nombre} onError={() => setBroken(true)} />
      : <div className="store-image-placeholder"><span aria-hidden="true">▧</span><small>Sin fotografía</small></div>}
  </div>;
}

