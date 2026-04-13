# Curator MMM: Bayesian Marketing Mix Modeling & Intelligence Platform

**Curator MMM** is a dual-surface platform designed to quantify marketing impact and optimize cross-channel budget allocation. It combines a robust **Bayesian MMM engine** built with Python and PyMC with a high-performance **Next.js web dashboard** for real-time market intelligence and strategic planning.

---

## Core Features

- **Bayesian Attribution Engine:** Leverages Markov Chain Monte Carlo (MCMC) sampling to estimate channel-specific ROI with full credible intervals.
- **Budget Optimization:** Uses SciPy-powered constrained minimization to find the optimal spend allocation that maximizes predicted revenue.
- **Dynamic Market Intelligence:** A Next.js dashboard integrated with Yahoo Finance, NewsAPI, and Groq AI (Llama 3.3) for live company analysis.
- **Adstock & Saturation Modeling:** Implements geometric decay and Hill functions to capture lagged effects and diminishing returns of advertising spend.
- **Custom SVG Visualization:** High-performance, hand-written SVG charts with Framer Motion animations—no external charting libraries used.

---

## 🖥️ Dashboard & Visuals

### 1. Market Intelligence Overview
The main dashboard provides a unified view of company KPIs, price trends, and AI-generated strategic insights.
![Market Intelligence Overview](Screenshot%202026-04-13%20110726.png)

### 2. Channel Attribution
Detailed breakdown of marketing spend effectiveness, utilizing Bayesian posterior inference to decompose revenue by channel.
![Channel Attribution](Screenshot%202026-04-13%20110758.png)

### 3. Budget Optimization
Strategic recommendations for spend allocation based on the fitted model's ROI estimates and live market conditions.
![Budget Optimization](Screenshot%202026-04-13%20110820.png)

### 4. Scenario Planning
Risk assessment and "what-if" analysis powered by Groq AI to evaluate potential marketing strategies under different market snapshots.
![Scenario Planning](Screenshot%202026-04-13%20110835.png)

---

## 🛠️ Tech Stack

### **Data Science & Modeling (Python)**
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Probabilistic Programming** | `PyMC`, `ArviZ` | Bayesian hierarchical modeling & MCMC diagnostics |
| **Optimization** | `SciPy` | Constrained budget minimization |
| **Data Processing** | `Pandas`, `NumPy`, `Scikit-learn` | ETL, feature engineering, and adstock transforms |
| **UI/UX** | `Streamlit`, `Plotly` | Interactive internal modeling dashboard |

### **Web Engineering (TypeScript/Node.js)**
| Component | Technology | Role |
| :--- | :--- | :--- |
| **Framework** | `Next.js 15` (App Router) | Server-side rendering & API route handling |
| **Frontend** | `React 19`, `Tailwind CSS` | Component-based UI and utility-first styling |
| **Animation** | `Framer Motion` | Fluid transitions and interactive SVG elements |
| **AI Integration** | `Groq SDK` (Llama 3.3) | LLM-powered marketing insight generation |

---

## 📐 System Architecture

### **Bayesian MMM Pipeline**
1.  **Data Ingestion:** Raw weekly spend and revenue data (supports synthetic data generation for testing).
2.  **Transformation:** Application of **Geometric Adstock** (carry-over) and **Hill Saturation** (diminishing returns) functions.
3.  **Inference:** Bayesian parameter estimation using the **NUTS (No-U-Turn) sampler**.
4.  **Attribution:** Posterior revenue decomposition to calculate ROI and contribution per channel.

### **Web Intelligence Flow**
The dashboard utilizes a **Server + Client split** for optimal performance:
- **Server-side:** Fetches live data from Yahoo Finance and NewsAPI; generates structured JSON insights via Groq AI.
- **Client-side:** Manages global state via `React Context` and renders high-performance SVG charts with custom normalization logic.

---

## 📂 Project Structure

```text
mmm_project/
├── src/                # Bayesian MMM core (model.py, optimizer.py, transforms.py)
├── web/                # Next.js Dashboard (App Router, Tailwind, Framer Motion)
├── data/               # Data pipeline & synthetic generators
├── outputs/            # Model artifacts (MCMC traces, ROI tables)
└── app.py              # Streamlit modeling interface
```

---

## 📈 Key Technical Achievements
- **No-Library Charts:** Built a custom SVG charting engine from scratch to ensure zero-dependency, high-performance visualizations.
- **Bayesian Rigor:** Moved beyond simple linear regression to a probabilistic model that quantifies uncertainty in marketing ROI.
- **AI-Driven Insights:** Successfully integrated LLMs to provide context-aware strategic recommendations based on live market news.
