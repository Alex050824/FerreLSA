import React, { useEffect, useMemo, useRef, useState } from 'react';

function getOptions(children) {
  return React.Children.toArray(children).flatMap(child => {
    if (!React.isValidElement(child)) return [];
    if (child.type === React.Fragment) return getOptions(child.props.children);
    if (child.type !== 'option') return [];
    return [{ value: String(child.props.value ?? child.props.children ?? ''), label: child.props.children, disabled: child.props.disabled }];
  });
}

export default function DropdownSelect({ children, value, onChange, disabled = false, required = false, className = '', ...props }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const options = useMemo(() => getOptions(children), [children]);
  const selected = options.find(option => option.value === String(value ?? '')) || options[0];

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = event => { if (!rootRef.current?.contains(event.target)) setOpen(false); };
    const closeOnEscape = event => { if (event.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', closeOnOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOnOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  const selectOption = option => {
    if (option.disabled) return;
    onChange?.({ target: { value: option.value } });
    setOpen(false);
  };

  const handleKeyDown = event => {
    if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(event.key)) {
      event.preventDefault();
      if (!open) { setOpen(true); return; }
      const enabled = options.filter(option => !option.disabled);
      const current = enabled.findIndex(option => option.value === selected?.value);
      const offset = event.key === 'ArrowUp' ? -1 : 1;
      if (event.key === 'Enter' || event.key === ' ') selectOption(enabled[Math.max(0, current)]);
      else {
        const next = enabled[(current + offset + enabled.length) % enabled.length];
        if (next) onChange?.({ target: { value: next.value } });
      }
    }
  };

  return (
    <div className={`ui-select ${className}`.trim()} ref={rootRef}>
      <button
        type="button"
        className="ui-select__trigger"
        role="combobox"
        aria-label={props['aria-label']}
        aria-required={required || undefined}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={open ? props.id ? `${props.id}-options` : undefined : undefined}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        onClick={() => setOpen(current => !current)}
      >
        <span>{selected?.label ?? ''}</span>
        <i className={`ui-select__chevron${open ? ' is-open' : ''}`} aria-hidden="true" />
      </button>
      {open && (
        <div className="ui-select__menu" role="listbox" id={props.id ? `${props.id}-options` : undefined}>
          {options.map((option, index) => {
            const isSelected = option.value === String(value ?? '');
            return <button type="button" role="option" aria-selected={isSelected} disabled={option.disabled}
              className={`ui-select__option${isSelected ? ' is-selected' : ''}`}
              key={`${option.value}-${index}`} onClick={() => selectOption(option)}>
              <span>{option.label}</span>{isSelected && <span aria-hidden="true">✓</span>}
            </button>;
          })}
        </div>
      )}
    </div>
  );
}
