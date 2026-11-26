"""Gráfico de barras accesible para el resumen de sentimiento."""

from html import escape


_CATEGORIAS = (
    ("Positivo", "positivo"),
    ("Negativo", "negativo"),
    ("Neutral", "neutral"),
    ("Revisar", "revisar"),
)


def grafico_resultados(conteo, total):
    """Genera HTML autocontenido con barras y valores visibles.

    Solo se muestran las categorías conocidas. Los comentarios marcados para
    revisión forman su propia categoría y no se suman a los otros sentimientos.
    """
    if not isinstance(total, int) or total < 0:
        raise ValueError("El total debe ser un entero no negativo.")
    valores = []
    for etiqueta, clase in _CATEGORIAS:
        valor = conteo.get(etiqueta, 0)
        if not isinstance(valor, int) or not 0 <= valor <= total:
            raise ValueError("Los conteos deben ser enteros entre cero y el total.")
        porcentaje = valor * 100 / total if total else 0.0
        valores.append((etiqueta, clase, valor, porcentaje))

    filas = "".join(
        f"<li class='grafico-fila'><span class='grafico-nombre'>{escape(etiqueta)}</span>"
        f"<span class='grafico-pista' aria-hidden='true'><span class='grafico-barra {clase}' "
        f"style='width:{porcentaje:.3f}%'></span></span>"
        f"<span class='grafico-valor'>{valor} ({porcentaje:.1f}%)</span></li>"
        for etiqueta, clase, valor, porcentaje in valores
    )
    aviso = "<p class='grafico-vacio'>Todavía no hay comentarios para mostrar.</p>" if total == 0 else ""
    return """<style>
    .grafico { margin: 24px 0; padding: 20px; border: 1px solid #dce3ef;
        border-radius: 14px; background: #f8faff; }
    .grafico h2 { margin: 0 0 6px; font-size: 1.2rem; }
    .grafico-intro { margin: 0 0 18px; color: #526078; font-size: .9rem; }
    .grafico-lista { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }
    .grafico-fila { display: grid; grid-template-columns: minmax(76px, 100px) 1fr auto;
        gap: 12px; align-items: center; font-size: .95rem; }
    .grafico-nombre { font-weight: 600; }
    .grafico-valor { min-width: 80px; text-align: right; font-variant-numeric: tabular-nums; }
    .grafico-pista { display: block; height: 18px; border-radius: 9px; background: #e2e8f2; overflow: hidden; }
    .grafico-barra { display: block; height: 100%; border-radius: 9px; }
    .grafico-barra.positivo { background: #198754; }
    .grafico-barra.negativo { background: #cb3d4d; }
    .grafico-barra.neutral { background: #4776bb; }
    .grafico-barra.revisar { background: #c18112; }
    .grafico-vacio { color: #526078; margin: 15px 0 0; }
    @media (max-width: 480px) {
        .grafico { padding: 16px; }
        .grafico-fila { grid-template-columns: 1fr auto; gap: 6px 10px; }
        .grafico-pista { grid-column: 1 / -1; grid-row: 2; }
    }
    </style><section class='grafico' aria-labelledby='titulo-grafico'>
    <h2 id='titulo-grafico'>Distribución de comentarios</h2>
    <p class='grafico-intro'>Cantidad y porcentaje del total analizado</p>
    <ul class='grafico-lista'>""" + filas + "</ul>" + aviso + "</section>"
