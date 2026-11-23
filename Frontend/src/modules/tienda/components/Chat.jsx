import React, { useState } from 'react';
import { id } from '../utils.js';

export default function Chat() {
  const [chatOpen, setChatOpen] = useState(false);
  const [chatText, setChatText] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  function submitChat(event) {
    event.preventDefault();
    if (!chatText.trim()) return;
    setChatMessages(previous => [...previous, { id: id(), text: chatText.trim() }]);
    setChatText('');
  }
  return <>
    {chatOpen && <section className="store-chat" aria-label="Ventana de chat"><div className="store-chat-header"><div><strong>¿Necesitás ayuda?</strong><small>Chat de demostración</small></div><button onClick={() => setChatOpen(false)} aria-label="Cerrar chat">×</button></div><div className="store-chat-body"><p className="store-chat-reply">¡Hola! La conexión con nuestro asistente estará disponible más adelante.</p>{chatMessages.map(message => <p className="store-chat-message" key={message.id}>{message.text}</p>)}</div><form onSubmit={submitChat}><input aria-label="Mensaje" value={chatText} onChange={event => setChatText(event.target.value)} placeholder="Escribí tu mensaje..." maxLength={500} /><button type="submit">Enviar</button></form></section>}
    <button className="store-chat-toggle" onClick={() => setChatOpen(value => !value)} aria-expanded={chatOpen} aria-label={chatOpen ? 'Cerrar chat' : 'Abrir chat'}>{chatOpen ? '×' : '✉'}</button>
  </>;
}
