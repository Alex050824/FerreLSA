
import React, { useState } from 'react';
import { id } from '../utils.js';

// Obtener la cookie de seguridad de Django
function obtenerCookie(nombre) {
  const cookie = document.cookie
    .split('; ')
    .find(valor => valor.startsWith(nombre + '='));

  return cookie
    ? decodeURIComponent(cookie.substring(nombre.length + 1))
    : null;
}

export default function Chat() {
  const [chatOpen, setChatOpen] = useState(false);
  const [chatText, setChatText] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [enviando, setEnviando] = useState(false);

  // Enviar preguntas al backend de Django
  async function submitChat(event) {
    event.preventDefault();

    const pregunta = chatText.trim();

    if (!pregunta || enviando) return;

    // Mostrar la pregunta del usuario
    setChatMessages(previous => [
      ...previous,
      { id: id(), tipo: 'usuario', text: pregunta }
    ]);

    setChatText('');
    setEnviando(true);

    try {
      // Obtener la cookie CSRF de Django
      const csrfRespuesta = await fetch('/api/chatbot/csrf/', {
        credentials: 'same-origin'
      });

      if (!csrfRespuesta.ok) {
        throw new Error('No se pudo obtener la protección CSRF.');
      }

      const csrfToken = obtenerCookie('csrftoken');

      if (!csrfToken) {
        throw new Error('No se encontró el token CSRF.');
      }

      // Enviar la pregunta a Qwen mediante Django
      const respuesta = await fetch('/api/chatbot/preguntar/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ pregunta })
      });

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(datos.error || 'Error al consultar el chatbot.');
      }

      // Mostrar la respuesta generada por Qwen
      setChatMessages(previous => [
        ...previous,
        {
          id: id(),
          tipo: 'bot',
          text: datos.respuesta
        }
      ]);

    } catch (error) {
      console.error('Error del chatbot:', error);

      setChatMessages(previous => [
        ...previous,
        {
          id: id(),
          tipo: 'bot',
          text: 'No se pudo consultar el asistente. Verificá que Django esté funcionando.'
        }
      ]);

    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      {chatOpen && (
        <section className="store-chat" aria-label="Ventana de chat">

          <div className="store-chat-header">
            <div>
              <strong>¿Necesitás ayuda?</strong>
              <small>Asistente virtual FerreLSA</small>
            </div>

            <button
              onClick={() => setChatOpen(false)}
              aria-label="Cerrar chat"
            >
              ×
            </button>
          </div>

          <div className="store-chat-body" aria-live="polite">

            <p className="store-chat-reply">
              ¡Hola! Soy el asistente virtual de FerreLSA.
              Preguntame sobre nuestros productos, precios y disponibilidad.
            </p>

            {chatMessages.map(message => (
              <p
                className={
                  message.tipo === 'bot'
                    ? 'store-chat-reply'
                    : 'store-chat-message'
                }
                key={message.id}
              >
                {message.text}
              </p>
            ))}

            {enviando && (
              <p className="store-chat-reply" role="status">
                Consultando inventario...
              </p>
            )}

          </div>

          <form onSubmit={submitChat}>
            <input
              aria-label="Mensaje"
              value={chatText}
              onChange={event => setChatText(event.target.value)}
              placeholder="Escribí tu mensaje..."
              maxLength={300}
            />

            <button type="submit" disabled={enviando}>
              {enviando ? 'Enviando...' : 'Enviar'}
            </button>
          </form>

        </section>
      )}

      <button
        className="store-chat-toggle"
        onClick={() => setChatOpen(value => !value)}
        aria-expanded={chatOpen}
        aria-label={chatOpen ? 'Cerrar chat' : 'Abrir chat'}
      >
        {chatOpen ? '×' : '✉'}
      </button>
    </>
  );
}
