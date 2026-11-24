export const money = value => new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC' }).format(Number(value) || 0);
export const id = () => Date.now() + Math.floor(Math.random() * 1000);
export const quantity = value => Math.round(Number(value) * 1000) / 1000;
export const amount = value => Math.round((Number(value) + Number.EPSILON) * 100) / 100;
export const customerName = user => user ? `${user.nombre || ''} ${user.apellido || ''}`.trim() : 'Cliente de demostración';
