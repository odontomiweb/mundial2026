# 📘 Guía simple — Web Mundial 2026

Hola Tomás. Esta es tu página del Mundial. Acá te explico todo en simple.

## ¿Qué tiene la página?
- **Hoy**: los partidos del día y los próximos.
- **Calendario**: los 72 partidos de la fase de grupos, con tu hora (Chile).
- **Grupos**: las tablas de posiciones (se llenan solas con los resultados),
  las barras de probabilidad y un botón para ver **tus apuntes a mano**.
- **Tips**: datos curiosos y tus notas.

## Los marcadores se actualizan SOLOS
Una vez publicada en GitHub, un robot (GitHub Actions) revisa los resultados
cada 2 horas y actualiza las tablas. Tú no tienes que hacer nada.

Para que funcione necesita una **clave gratis** (se saca en 2 minutos):
1. Entra a **https://www.football-data.org/client/register**
2. Pon tu correo y registra. Te llega una clave (un código largo).
3. En tu repo de GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `FOOTBALL_DATA_TOKEN`
   - Secret: pega el código
   - Guardar.

¡Listo! El robot ya puede leer los resultados.

## ¿Cómo agrego una nota mía?
Dile a Claude: *"agrega esta nota al Mundial: ..."* y la pone en la sección Tips.
(O se edita el archivo `data/tips.json`, en la parte de `"notas"`.)

## ¿Cómo veo la página en mi computador?
Abre la carpeta y haz doble clic en `abrir.bat` (o pídele a Claude que la abra).
No abras `index.html` directo: necesita un mini servidor para cargar los datos.

## Los recordatorios de WhatsApp
Los recordatorios diarios de madrugada con los partidos del día ya los tienes
en tu proyecto de n8n. Esta página y ese bot son cosas separadas que se
complementan.

---
Hecho con ⚽
