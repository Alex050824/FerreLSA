import React, { useEffect, useState } from 'react';
import Icon from './components/Icons.jsx';

const CATEGORIES = [
  { name: 'Herramientas', text: 'Para construir, reparar y trabajar con precisión.', icon: 'tools', shade: 'peach', number: '01' },
  { name: 'Pinturas', text: 'Opciones para renovar y darle vida a cada espacio.', icon: 'paint', shade: 'blue', number: '02' },
  { name: 'Electricidad', text: 'Artículos para instalaciones y mantenimiento.', icon: 'electricity', shade: 'yellow', number: '03' },
  { name: 'Plomería', text: 'Suministros para conexiones y reparaciones.', icon: 'plumbing', shade: 'mint', number: '04' },
  { name: 'Construcción', text: 'Materiales que acompañan cada etapa de una obra.', icon: 'building', shade: 'lavender', number: '05' },
  { name: 'Suministros', text: 'Complementos útiles para tareas del día a día.', icon: 'supplies', shade: 'gray', number: '06' },
];

const LINKS = [
  { label: 'Inicio', href: '#inicio' },
  { label: 'Nosotros', href: '#nosotros' },
  { label: 'Categorías', href: '#categorias' },
  { label: 'Misión y visión', href: '#mision-vision' },
];

function Brand({ compact = false }) {
  return (
    <a href="#inicio" className={`brand ${compact ? 'brand--compact' : ''}`} aria-label="FerreLSA, volver al inicio">
      <img src="/assets/emblema-ferrelsa.png" alt="" className="brand__mark" />
      <span className="brand__name"><span className="brand__word">Ferre<span>LSA</span></span><small>FERRETERÍA</small></span>
    </a>
  );
}

function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    const onEscape = (event) => event.key === 'Escape' && setMenuOpen(false);
    document.addEventListener('keydown', onEscape);
    return () => document.removeEventListener('keydown', onEscape);
  }, []);

  return (
    <>
      <div className="topline"><div className="container topline__inner"><span>FERRELSA <span className="topline__dot">✦</span> PARA CADA PROYECTO</span><span className="topline__right">Construcción · Reparación · Mantenimiento</span></div></div>
      <header className="header">
        <div className="container header__inner">
          <Brand />
          <nav className={`nav ${menuOpen ? 'nav--open' : ''}`} id="primary-nav" aria-label="Navegación principal">
            {LINKS.map(link => <a key={link.href} onClick={() => setMenuOpen(false)} href={link.href} className="nav__link">{link.label}</a>)}
            <a className="button button--small button--primary nav__cta" href="#categorias" onClick={() => setMenuOpen(false)}>Explorar productos <Icon name="upRight" size={16} /></a>
          </nav>
          <button type="button" className="menu-toggle" aria-expanded={menuOpen} aria-controls="primary-nav" aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'} onClick={() => setMenuOpen(!menuOpen)}><Icon name={menuOpen ? 'close' : 'menu'} size={26}/></button>
        </div>
      </header>
    </>
  );
}

function Hero() {
  return (
    <section className="hero" id="inicio">
      <div className="container hero__grid">
        <div className="hero__copy">
          <div className="eyebrow"><span className="eyebrow__line"/> TU FERRETERÍA DE CONFIANZA</div>
          <h1>Grandes ideas.<br/><span>Buenos proyectos.</span><br/>Las herramientas correctas.</h1>
          <p>En <strong>FerreLSA</strong> encontrás productos y materiales para construir, reparar y darle forma a lo que imaginás. Desde pequeñas mejoras en casa hasta trabajos profesionales.</p>
          <div className="hero__actions">
            <a href="#categorias" className="button button--primary">Explorar categorías <Icon name="arrow" size={19}/></a>
            <a href="#nosotros" className="button button--outline">Conocé FerreLSA <Icon name="upRight" size={18}/></a>
          </div>
          <div className="hero__micro"><span className="micro-icon"><Icon name="check" size={14}/></span> Productos para el hogar y el trabajo profesional</div>
        </div>
        <div className="hero__visual" aria-label="Logo oficial de FerreLSA presentado sobre fondo azul">
          <div className="visual__grid" aria-hidden="true"/>
          <div className="visual__orbit visual__orbit--outer" aria-hidden="true" />
          <div className="visual__orbit visual__orbit--inner" aria-hidden="true" />
          <div className="visual__corner visual__corner--one" aria-hidden="true"/>
          <div className="visual__corner visual__corner--two" aria-hidden="true"/>
          <div className="visual__sticker visual__sticker--top"><span className="sticker__dot"/> HAGAMOS QUE SUCEDA</div>
          <div className="visual__logo"><img src="/assets/logo-ferrelsa.png" alt="Logotipo de la ferretería FerreLSA: engranaje, herramientas y nombre en azul y naranja" /></div>
          <div className="visual__sticker visual__sticker--bottom"><Icon name="sparkle" size={18}/> Todo empieza con una idea</div>
          <div className="visual__index" aria-hidden="true">F / LSA · 2026</div>
        </div>
      </div>
      <div className="container hero__bottom"><span>FERRETERÍA + SOLUCIONES</span><span className="hero__scroll">Descubrí más <span className="scroll-line"/></span></div>
    </section>
  );
}

function IntroBand() {
  return (
    <section className="intro-band" aria-label="Qué ofrece FerreLSA">
      <div className="container intro-band__content">
        <div className="intro-band__statement">Una ferretería para <em>cada etapa</em> de tu proyecto.</div>
        <div className="intro-band__items">
          <div><Icon name="tools" size={22}/><span>HERRAMIENTAS</span></div>
          <div><Icon name="building" size={22}/><span>MATERIALES</span></div>
          <div><Icon name="supplies" size={22}/><span>SUMINISTROS</span></div>
        </div>
      </div>
    </section>
  );
}

function About() {
  return (
    <section className="section about" id="nosotros">
      <div className="container about__grid">
        <div className="about__art" aria-hidden="true">
          <div className="about__frame">
            <div className="about__frame-head">DISEÑADO PARA CONSTRUIR <span>✦</span></div>
            <div className="about__bigletter">F<span>.</span></div>
            <div className="about__line-art"><Icon name="tools" size={95} strokeWidth={1} /></div>
            <span className="about__art-text">FERRELSA — FERRETERÍA</span>
          </div>
          <div className="about__badge"><Icon name="check" size={21} strokeWidth={2.5}/><span>PARA HOGARES<br/>Y PROFESIONALES</span></div>
        </div>
        <div className="about__content">
          <span className="section-tag"><span/> CONOCENOS</span>
          <h2>Más que materiales,<br/><span>soluciones para avanzar.</span></h2>
          <p>FerreLSA es una ferretería dedicada a la comercialización de productos para la <strong>construcción, reparación y mantenimiento</strong> de viviendas e instalaciones.</p>
          <p>Atendemos las necesidades tanto de personas que trabajan en sus hogares como de profesionales independientes del sector de la construcción.</p>
          <div className="about__highlights">
            <div><span className="highlight__icon"><Icon name="tools" size={23}/></span><div><strong>Para tus proyectos</strong><small>Del mantenimiento diario a obras de construcción.</small></div></div>
            <div><span className="highlight__icon"><Icon name="heart" size={23}/></span><div><strong>Para diferentes necesidades</strong><small>Productos para clientes particulares y profesionales.</small></div></div>
          </div>
          <a className="text-link" href="#mision-vision">Conocé lo que nos inspira <Icon name="arrow" size={18}/></a>
        </div>
      </div>
    </section>
  );
}

function Categories() {
  return (
    <section className="section categories" id="categorias">
      <div className="container">
        <div className="section-heading"><div><span className="section-tag"><span/> LO QUE ENCONTRÁS AQUÍ</span><h2>Todo para poner<br/><span>manos a la obra.</span></h2></div><p>Conocé las principales líneas de productos que forman parte de nuestra ferretería.</p></div>
        <div className="category-grid">
          {CATEGORIES.map(item => <article key={item.name} className={`category-card category-card--${item.shade}`}>
            <span className="category-card__num">{item.number} / 06</span>
            <div className="category-card__icon"><Icon name={item.icon} size={43} strokeWidth={1.5}/></div>
            <div className="category-card__body"><h3>{item.name}</h3><p>{item.text}</p></div>

          </article>)}
        </div>
        <p className="category-footnote"><Icon name="sparkle" size={16}/> Estas son categorías generales del proyecto FerreLSA; no corresponden a un catálogo de existencias en tiempo real.</p>
      </div>
    </section>
  );
}

function MissionVision() {
  return (
    <section className="section values" id="mision-vision">
      <div className="container">
        <div className="values__head"><span className="section-tag section-tag--light"><span/> LO QUE NOS MUEVE</span><h2>Nuestra esencia,<br/><em>nuestro rumbo.</em></h2><p>Una propuesta de misión y visión que resume el propósito y la dirección que buscamos para FerreLSA.</p></div>
        <div className="values__grid">
          <article className="value-card"><div className="value-card__head"><span className="value-card__icon"><Icon name="compass" size={26}/></span><span className="value-card__index">01 / NUESTRO PROPÓSITO</span></div><h3>Misión</h3><p>Ofrecer productos y materiales de ferretería para la construcción, reparación y mantenimiento, respondiendo a las necesidades de clientes particulares y profesionales, con una atención orientada a facilitar cada proyecto.</p><span className="value-card__rule"/></article>
          <article className="value-card"><div className="value-card__head"><span className="value-card__icon"><Icon name="star" size={26}/></span><span className="value-card__index">02 / HACIA DÓNDE VAMOS</span></div><h3>Visión</h3><p>Consolidarnos como una ferretería reconocida por acompañar los proyectos de nuestros clientes, con una oferta útil de productos y una gestión cada vez más organizada, eficiente y apoyada en tecnología.</p><span className="value-card__rule"/></article>
        </div>
      </div>
    </section>
  );
}

function Innovation() {
  return (
    <section className="section innovation">
      <div className="container innovation__inner"><div className="innovation__icon"><Icon name="chart" size={32}/></div><div className="innovation__copy"><span>EVOLUCIONANDO CON CADA PROYECTO</span><h2>Una ferretería que también mira al futuro.</h2><p>Como parte de su evolución, FerreLSA contempla el desarrollo de un sistema ERP para integrar las operaciones de ventas, inventario, compras, facturación y administración comercial.</p></div><a href="#inicio" className="innovation__link" aria-label="Volver al inicio"><Icon name="upRight" size={24}/></a></div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer"><div className="container"><div className="footer__upper"><div><Brand compact/><p>Para quienes imaginan, construyen y transforman sus espacios.</p></div><nav aria-label="Enlaces del pie de página">{LINKS.map(link => <a href={link.href} key={link.href}>{link.label}</a>)}</nav></div><div className="footer__bottom"><span>© {new Date().getFullYear()} FerreLSA. Proyecto académico.</span><span>Hecho para construir algo mejor. <span className="footer__asterisk">✳</span></span></div></div></footer>
  );
}

export default function App() {
  return <><Header/><main><Hero/><IntroBand/><About/><Categories/><MissionVision/><Innovation/></main><Footer/></>;
}
