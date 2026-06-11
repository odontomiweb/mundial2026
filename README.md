# ⚽ Mundial 2026 — Fase de Grupos

Página web con el **calendario, tablas de posiciones, probabilidades y tips**
de la fase de grupos del Mundial 2026 (EE.UU. · México · Canadá).

- Horarios mostrados en la hora local de quien la abre.
- Tablas de posiciones que se calculan solas con los resultados.
- **Resultados actualizados automáticamente** con GitHub Actions.

👉 Guía para usarla y publicarla: ver **[GUIA.md](GUIA.md)**.

## Estructura
```
index.html          Página principal
css/style.css        Estilos
js/app.js            Lógica (carga datos y arma todo)
data/groups.json     Los 12 grupos y sus selecciones
data/matches.json    Los 72 partidos (con marcadores)
data/tips.json       Probabilidades, comentarios y notas
imagenes/            Apuntes a mano + infografías
scripts/             Generador de datos y actualizador de resultados
.github/workflows/   Robot que actualiza los marcadores
```

## Datos
Calendario y grupos: sorteo oficial del 5 de diciembre de 2025.
Resultados en vivo: [football-data.org](https://www.football-data.org) (plan gratis).
