import React from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Typography,
} from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import CloseIcon from "@mui/icons-material/Close";

const SECTIONS = [
  {
    title: "¿Qué hace esta app?",
    body: "Analiza la rentabilidad de tu tienda cargando los reportes de ventas y gastos exportados desde FUDO. Calcula automáticamente EBITDA, CMV, márgenes por producto y simula cuántas unidades adicionales necesitas vender para alcanzar el equilibrio financiero o una meta de rentabilidad del 25%.",
  },
  {
    title: "Archivos necesarios (desde FUDO)",
    list: [
      [
        "Ventas",
        'Exportar reporte "Adiciones" (.xls). Contiene el detalle de cada ítem vendido con precio, costo de ingredientes y canal de venta.',
      ],
      [
        "Gastos",
        'Exportar reporte "Gastos" (.xlsx). Contiene todos los gastos registrados con proveedor, categoría e importe. Se omiten automáticamente los préstamos de socios y compras de activo fijo.',
      ],
    ],
  },
  {
    title: "Cálculos y fórmulas",
    formulas: [
      [
        "IVA (19%)",
        'Los precios de venta en FUDO incluyen IVA. Todos los valores "sin IVA" se obtienen dividiendo por 1.19, permitiendo analizar en términos netos. El IVA no es ingreso real — lo recaudas y lo devuelves al SII.',
      ],
      [
        "CMV — Costo de Mercadería Vendida",
        "CMV% = (Costo ingredientes sin IVA) / (Ingreso sin IVA) × 100. Mide qué fracción de cada peso de venta se destina a ingredientes y modificadores. Rango saludable para restaurantes: 25–35%.",
      ],
      [
        "Comisión Uber Eats (30%)",
        'Los pedidos con origen "uber_eats" tienen un 30% del ingreso descontado como comisión. Esta comisión se suma al costo total del ítem y reduce el margen bruto.',
      ],
      [
        "Margen bruto sin IVA",
        "Ingreso sin IVA − COGS sin IVA (ingredientes + modificadores + comisiones Uber Eats). Aparece en las tablas de producto para análisis por ítem.",
      ],
      [
        "EBITDA",
        "EBITDA = Ingresos sin IVA − Gastos operacionales (del archivo de gastos). Los gastos incluyen materia prima, sueldos, arriendo y otros costos reales pagados. Préstamos de socios y activo fijo se excluyen por ser financiamiento/inversión. El % se calcula sobre el ingreso sin IVA.",
      ],
      [
        "Break-even y simulador (en tickets)",
        "El break-even se calcula en tickets (pedidos únicos, identificados por Id. Venta), no en unidades individuales. Ticket promedio = ingresos sin IVA / tickets únicos. Contribución por ticket = ticket promedio − CMV promedio. Break-even: tickets_extra = −EBITDA / contribución. Para EBITDA 25%: tickets_extra = (0.25·I − E) / (contribución − 0.25·ticket). El simulador de precio y costos se activa solo cuando ambos archivos están cargados; el aumento de precio aplica únicamente a Especialidades.",
      ],
    ],
  },
  {
    title: "Vistas y gráficos",
    list: [
      [
        "Ventas / Gastos / Precios",
        "Tablas accesibles desde el AppBar. Ventas: agregado por producto con búsqueda y orden por cualquier columna. Gastos: detalle por tipo (Operacional / Préstamo / Activo Fijo). Precios: precio neto promedio, CMV% y precio real en Uber Eats, filtrable por canal (local / Uber Eats) y categoría.",
      ],
      [
        "Evolución diaria",
        "Gráfico de barras con la actividad de cada día del mes + línea de promedio móvil de 7 días para suavizar la tendencia. Alterna entre ingresos y cantidad de ventas.",
      ],
      [
        "Ventas por hora y día de la semana",
        "Distribución acumulada por hora del día y por día de la semana. Útil para identificar los horarios y días pico.",
      ],
      [
        "Top Especialidades y Top Extras",
        "Gráficos separados por categoría (Especialidades = pizzas, Extras = complementos) tanto por unidades como por ingresos. Permite comparar el desempeño de cada línea de producto de forma independiente.",
      ],
      [
        "Simulador de Precio y Costos",
        "Simula el impacto de subir el precio de venta de Especialidades (en CLP con IVA) y/o un alza porcentual en el costo de ingredientes. Muestra el rango de fechas exacto del período analizado, el total de tickets y unidades de Especialidades. La tabla compara Actual vs. Simulado para: Ingreso s/IVA, CMV, Ticket promedio, Contribución % y EBITDA.",
      ],
      [
        "Descargar",
        "Menú desplegable en el AppBar con tres opciones: Reporte del Mes (PDF con KPIs, break-even en tickets, gastos y tablas completas de productos), Especialidades (Excel con todos los productos y cálculos de margen) y Extras (Excel equivalente para complementos). El nombre del archivo PDF refleja el período real de los datos, no la fecha actual.",
      ],
    ],
  },
  {
    title: "Asesor de Promociones Uber Eats",
    formulas: [
      [
        "¿Qué hace?",
        "Analiza las ventas del período cargado y sugiere los 5 mejores productos por categoría para incluir en promociones de Uber Eats. También muestra el patrón horario de pedidos en el canal y compara el ticket promedio Uber Eats vs. local.",
      ],
      [
        "Puntuación compuesta (score 0–100)",
        "Combina tres factores: Margen bruto (50 %) — qué tanto queda después de ingredientes y comisión Uber Eats; Eficiencia de costo (30 %) — inverso del CMV (menor costo = mayor puntaje); Volumen relativo (20 %) — popularidad del producto frente al más vendido del período. Fórmula: score = margen% × 0.5 + (100 − cmv%) × 0.3 + volumen_relativo × 0.2.",
      ],
      [
        "Interpretación del score",
        "Verde (≥ 80): excelente candidato, alto margen y buen volumen. Amarillo (≥ 65): buen candidato con alguna restricción. Gris (< 65): posible pero con trade-offs. El ícono ⓘ junto al botón de refresco muestra esta explicación en la pantalla.",
      ],
      [
        "Horas pico vs. oportunidad",
        "Naranja = horas con ≥ 60 % del volumen máximo de Uber Eats → lanzar promos flash aquí maximiza alcance. Azul = horas con actividad real pero menor al 50 % del pico → promos para llenar capacidad ociosa sin canibalizar precio en horas pico.",
      ],
      [
        "Ticket promedio por pedido",
        "Se calcula agrupando todos los ítems de un mismo Id. Venta antes de promediar, para que una orden con 3 productos cuente como un solo pedido. El objetivo de las promociones tipo bundle o combo es elevar este ticket en Uber Eats.",
      ],
    ],
  },
];

const HelpModal = ({ open, onClose }) => (
  <Dialog
    open={open}
    onClose={onClose}
    maxWidth="md"
    fullWidth
    PaperProps={{ sx: { bgcolor: "#1E293B", border: "1px solid #334155" } }}
  >
    <DialogTitle
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <HelpOutlineIcon color="primary" />
        <Typography variant="h6">Cómo funciona FUDO Analytics</Typography>
      </Box>
      <IconButton onClick={onClose} size="small">
        <CloseIcon fontSize="small" />
      </IconButton>
    </DialogTitle>

    <DialogContent dividers sx={{ borderColor: "#334155" }}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {SECTIONS.map(({ title, body, list, formulas }) => (
          <Box key={title}>
            <Typography variant="subtitle2" color="primary.main" sx={{ mb: 1 }}>
              {title}
            </Typography>

            {body && (
              <Typography variant="body2" color="text.secondary">
                {body}
              </Typography>
            )}

            {list && (
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                {list.map(([label, desc]) => (
                  <Box component="li" key={label} sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      <strong style={{ color: "#F1F5F9" }}>{label}:</strong>{" "}
                      <span style={{ color: "#94A3B8" }}>{desc}</span>
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {formulas && (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                {formulas.map(([label, desc]) => (
                  <Box key={label}>
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      sx={{ color: "#F1F5F9", mb: 0.3 }}
                    >
                      {label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {desc}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        ))}

        <Box
          sx={{
            bgcolor: "#F9731615",
            border: "1px solid #F9731640",
            borderRadius: 2,
            p: 2,
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: "#FBBF24", fontWeight: 600, mb: 0.5 }}
          >
            ⚠️ Los datos son efímeros
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Los archivos cargados se almacenan en la sesión del servidor
            (SQLite, 24 h). Al reiniciar el servidor o hacer clic en "Reiniciar"
            los datos se eliminan. Usa el botón PDF para guardar un snapshot
            antes de cerrar.
          </Typography>
        </Box>
      </Box>
    </DialogContent>

    <DialogActions sx={{ px: 3, py: 2 }}>
      <Button onClick={onClose} variant="contained" color="primary">
        Entendido
      </Button>
    </DialogActions>
  </Dialog>
);

export default HelpModal;
