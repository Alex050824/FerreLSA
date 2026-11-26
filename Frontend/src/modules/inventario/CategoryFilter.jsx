import React, { useEffect, useRef, useState } from 'react';

export default function CategoryFilter({ categories, value, onChange }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const selected = categories.find(category => String(category.id) === String(value));
  const options = [{ id: '', nombre: 'Todas las categorías' }, ...categories];

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = event => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = event => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', closeOnOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOnOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  return (
    <div className="inventory-category-filter">
      <span>Filtrar por categoría</span>
      <div className="inventory-category-combobox" ref={rootRef}>
        <button
          type="button"
          className="inventory-category-trigger"
          role="combobox"
          aria-label="Filtrar por categoría"
          aria-expanded={open}
          aria-controls="inventory-category-options"
          aria-haspopup="listbox"
          onClick={() => setOpen(current => !current)}
        >
          <span>{selected?.nombre || 'Todas las categorías'}</span>
          <i className={`inventory-category-chevron${open ? ' is-open' : ''}`} aria-hidden="true" />
        </button>
        {open && (
          <div className="inventory-category-menu" id="inventory-category-options" role="listbox" aria-label="Categorías">
            {options.map(category => {
              const isSelected = String(category.id) === String(value);
              return (
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`inventory-category-option${isSelected ? ' is-selected' : ''}`}
                  key={category.id || 'all'}
                  onClick={() => { onChange(category.id); setOpen(false); }}
                >
                  {category.nombre}
                  {isSelected && <span aria-hidden="true">✓</span>}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
