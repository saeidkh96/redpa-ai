from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(
    prefix="/memory/dashboard",
    tags=["Agent Memory Dashboard"],
)


@router.get(
    "",
    response_class=HTMLResponse,
)
async def memory_dashboard() -> HTMLResponse:
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>RedPA Agent Memory</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              margin: 0;
              background: #111827;
              color: #f9fafb;
            }
            main {
              max-width: 1100px;
              margin: 0 auto;
              padding: 32px;
            }
            h1 {
              margin-bottom: 8px;
            }
            .grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
              gap: 16px;
              margin-top: 24px;
            }
            .card {
              background: #1f2937;
              border: 1px solid #374151;
              border-radius: 12px;
              padding: 20px;
            }
            .value {
              font-size: 30px;
              font-weight: 700;
              margin-top: 8px;
            }
            pre {
              white-space: pre-wrap;
              word-break: break-word;
              background: #0f172a;
              padding: 16px;
              border-radius: 12px;
            }
          </style>
        </head>
        <body>
          <main>
            <h1>RedPA Agent Memory</h1>
            <p>Long-term, semantic, shared, and managed Agent Memory.</p>
            <div id="cards" class="grid"></div>
            <h2>Analytics</h2>
            <pre id="analytics">Loading...</pre>
          </main>
          <script>
            async function load() {
              const response = await fetch('/api/v1/memory/admin/analytics');
              const data = await response.json();

              document.getElementById('analytics').textContent =
                JSON.stringify(data, null, 2);

              const cards = [
                ['Total Memories', data.total_memories],
                ['Active', data.active_memories],
                ['Inactive', data.inactive_memories],
                ['Average Importance', data.average_importance]
              ];

              document.getElementById('cards').innerHTML = cards.map(
                ([label, value]) =>
                  `<div class="card">
                    <div>${label}</div>
                    <div class="value">${value}</div>
                  </div>`
              ).join('');
            }

            load().catch((error) => {
              document.getElementById('analytics').textContent =
                String(error);
            });
          </script>
        </body>
        </html>
        """
    )
