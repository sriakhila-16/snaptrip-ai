# Implementation Plan - SnapTrip AI (Smart Travel Companion)

SnapTrip AI is a modern, full-stack AI-powered travel companion web application built for local and international tourists. It combines multimodal vision AI (Google Gemini Vision) with local trip planning, budget tracking, and landmark discovery.

---

## 🏗️ Architecture & Directory Structure

```
promptwars/
├── .env.example                # Example environment variables (GEMINI_API_KEY)
├── .env                        # Local environment configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Complete setup, testing, and deployment guide
├── implementation_plan.md      # Architecture, database schema, and plan
├── app.py                      # Main Streamlit application entrypoint
├── database.py                 # SQLite database models, schemas, and helper queries
├── auth.py                     # Authentication logic (signup, login, password hashing, session state)
├── gemini_service.py           # Gemini 2.0/1.5 Flash Vision integration & structured JSON parser
├── components/                 # Reusable UI components & styling
│   ├── __init__.py
│   ├── styles.py               # Custom CSS for modern glassmorphism & responsive mobile layout
│   ├── trip_dashboard.py       # Trip setup, duration, currency & budget settings
│   ├── snap_identify.py        # Image uploader, camera snap, sample photos & AI landmark vision view
│   ├── itinerary_view.py       # Cumulative budget tracker, day spending summary & itinerary management
│   └── profile_view.py         # User profile, history of scans & saved trips
└── assets/                     # Static assets & sample images for instant demo testing
    ├── sample_taj_mahal.jpg
    ├── sample_eiffel_tower.jpg
    └── sample_colosseum.jpg
```

---

## 🔑 Environment Variables Configuration

The application uses `python-dotenv` to load secrets from `.env`.
Users can also input their Gemini API key directly into the application's sidebar setting if preferred.

```ini
# .env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🗄️ Database Schema (SQLite: `snaptrip.db`)

1. **`users` Table:**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `username`: TEXT UNIQUE NOT NULL
   - `email`: TEXT UNIQUE NOT NULL
   - `password_hash`: TEXT NOT NULL
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

2. **`trips` Table:**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL (FOREIGN KEY -> users.id)
   - `trip_name`: TEXT NOT NULL
   - `destination_city`: TEXT NOT NULL
   - `duration_days`: INTEGER DEFAULT 1
   - `budget_tier`: TEXT DEFAULT 'Moderate' (Budget, Moderate, Luxury, Custom)
   - `daily_budget_limit`: REAL NOT NULL
   - `currency`: TEXT DEFAULT 'USD'
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

3. **`landmark_scans` Table:**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER NOT NULL
   - `trip_id`: INTEGER (FOREIGN KEY -> trips.id)
   - `landmark_name`: TEXT NOT NULL
   - `location`: TEXT NOT NULL
   - `history_points`: TEXT (JSON serialized list of historical points)
   - `ticket_cost`: REAL DEFAULT 0.0
   - `transport_cost`: REAL DEFAULT 0.0
   - `food_cost`: REAL DEFAULT 0.0
   - `total_cost`: REAL DEFAULT 0.0
   - `currency`: TEXT DEFAULT 'USD'
   - `nearby_attractions`: TEXT (JSON serialized list of 3 recommendations)
   - `local_tips`: TEXT (JSON serialized list of tips)
   - `image_data`: TEXT (Base64 data or path)
   - `scanned_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

---

## 🤖 Gemini Vision AI Prompt & Structured Output

- **Model:** `gemini-2.0-flash` (with fallback to `gemini-1.5-flash`)
- **System Instruction / Structured JSON Schema:**
  Enforces deterministic JSON response:
  ```json
  {
    "landmark_name": "Taj Mahal",
    "location": "Agra, Uttar Pradesh, India",
    "history_and_significance": [
      "Built between 1632 and 1648 by Mughal emperor Shah Jahan in memory of his favorite wife Mumtaz Mahal.",
      "Recognized as a UNESCO World Heritage Site in 1983 and an iconic masterpiece of Mughal architecture.",
      "Attracts 7 to 8 million visitors a year from around the globe."
    ],
    "estimated_costs": {
      "ticket_fee": 15.0,
      "local_transport": 5.0,
      "food_snacks": 8.0,
      "total_estimate": 28.0,
      "currency": "USD",
      "notes": "Includes shoe covers and entry to main mausoleum."
    },
    "nearby_attractions": [
      {
        "name": "Agra Fort",
        "distance": "2.5 km (10 mins by auto-rickshaw)",
        "highlights": "Historic 16th-century Mughal fortress with royal residences.",
        "estimated_cost": 8.0,
        "why_recommended": "Complements the architectural history of the Taj Mahal."
      },
      {
        "name": "Mehtab Bagh",
        "distance": "7.5 km (across Yamuna River)",
        "highlights": "Charbagh garden complex offering sunset views of Taj Mahal.",
        "estimated_cost": 4.0,
        "why_recommended": "Stunning sunset photography angle with calm atmosphere."
      },
      {
        "name": "Itmad-ud-Daulah (Baby Taj)",
        "distance": "6 km (15 mins by taxi)",
        "highlights": "Exquisite marble inlay mausoleum preceding Taj Mahal.",
        "estimated_cost": 5.0,
        "why_recommended": "Less crowded architectural gem."
      }
    ],
    "insider_tips": [
      "Visit at sunrise to avoid heavy crowds and heat.",
      "Tripods and drone cameras are strictly prohibited on grounds."
    ]
  }
  ```

---

## 🎨 Frontend UI Tabs & Capabilities

1. **Authentication & Profile:**
   - Sign up / Log in with secure hashed passwords.
   - Guest mode enabled for quick zero-friction preview.
   - Profile tab displaying trip stats, total landmarks visited, and total spending.
2. **Trip Setup & Budgeting:**
   - Destination city input.
   - Trip duration slider (1 to 7+ days).
   - Budget level selector (Budget / Moderate / Luxury / Custom amount) with real-time daily budget calculation.
   - Currency switcher (USD $, EUR €, GBP £, INR ₹, JPY ¥, CAD $, AUD $).
3. **Snap & Identify:**
   - Dual input: Live Camera Snap (`st.camera_input`) OR Photo File Upload.
   - Quick sample buttons (Taj Mahal, Eiffel Tower, Colosseum) for 1-click test drive without needing local files.
   - Real-time AI analysis with cost breakdowns, historical facts, and 3 recommended nearby spots.
   - 1-click "Save to Trip Itinerary" action.
4. **Interactive Itinerary & Budget Summary:**
   - Real-time budget progress bar (Spent vs. Daily / Total Budget).
   - Filter by active trip.
   - Visual cards of each visited landmark with detailed notes.
   - Export itinerary as JSON or printable Markdown.

---

## 📋 Execution Steps

1. Verify dependency installation and setup `.env` / configuration.
2. Implement `database.py` with SQLite table creation and CRUD operations.
3. Implement `auth.py` with password hashing, login, and registration.
4. Implement `gemini_service.py` with Google GenAI SDK and robust fallback parsing.
5. Create sample images in `assets/` for seamless testing.
6. Build modular UI components in `components/` and main `app.py`.
7. Launch and test the web app, verifying authentication, trip setup, camera/file upload, AI parsing, and budget tracking.
8. Document setup and usage in `README.md`.

