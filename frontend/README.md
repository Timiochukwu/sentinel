# Sentinel Frontend

Modern 3D SaaS dashboard for the Nigerian Fraud Detection Platform.

## 🎨 Features

- **3D Graphics**: Animated wireframe sphere and particle field (1000 particles) using Three.js
- **Glass Morphism**: Frosted glass effects with blur and transparency
- **Smooth Animations**: Framer Motion for fluid UI transitions
- **Real-time Stats**: Live dashboard with fraud metrics and charts
- **Mobile Responsive**: Works perfectly on all screen sizes
- **Dark Theme**: Modern purple/pink gradient color scheme
- **Type-Safe**: Full TypeScript implementation

## 🛠️ Tech Stack

- **React 18** - UI library with hooks
- **TypeScript** - Type safety and better DX
- **Vite** - Lightning-fast dev server and build tool
- **Tailwind CSS** - Utility-first styling with custom theme
- **Framer Motion** - Animation library
- **Three.js + React Three Fiber** - 3D graphics
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **React Router** - Client-side routing
- **date-fns** - Date formatting

## 📦 Installation

```bash
# Install dependencies
npm install

# Or with yarn
yarn install
```

## 🚀 Development

```bash
# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Background3D.tsx # Three.js 3D background
│   │   ├── Layout.tsx       # Main layout with sidebar
│   │   └── StatCard.tsx     # Animated stat cards
│   ├── pages/               # Route pages
│   │   ├── Dashboard.tsx    # Main dashboard with charts
│   │   ├── Transactions.tsx # Transaction list with filters
│   │   ├── Analytics.tsx    # Analytics (placeholder)
│   │   ├── Settings.tsx     # Configuration panel
│   │   └── Login.tsx        # Authentication UI
│   ├── lib/
│   │   └── api.ts          # API client (Axios)
│   ├── types/
│   │   └── index.ts        # TypeScript types
│   ├── App.tsx             # Root component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles + Tailwind
├── package.json
├── tailwind.config.js      # Custom theme configuration
├── tsconfig.json           # TypeScript config
└── vite.config.ts          # Vite configuration
```

## 🎯 Key Components

### Background3D
Animated 3D background with:
- Rotating wireframe sphere
- 1000-particle field
- Auto-rotating orbit controls

### Layout
Main application layout featuring:
- Collapsible sidebar navigation
- Mobile-responsive menu
- Glass morphism design
- User profile section

### StatCard
Reusable metric cards with:
- Framer Motion animations
- Icon support (lucide-react)
- Trend indicators
- Hover effects

## 📊 Pages

### Dashboard
- 6 real-time stat cards
- Pie chart for risk distribution
- Bar chart for fraud types
- Performance metrics grid

### Transactions
- Filterable transaction list (all/high/medium/low)
- Search by transaction ID
- Risk level badges
- Decision indicators (approve/review/decline)
- Date formatting

### Settings
- API key display
- Webhook URL configuration
- ML model toggle
- Notification preferences

### Login
- Glassmorphism form design
- 3D animated background
- Email/password inputs
- Platform stats display

## 🔌 API Integration

The frontend connects to the Sentinel backend API:

```typescript
// src/lib/api.ts
const API_BASE_URL = 'http://localhost:8080'

// Available methods:
fraudAPI.getStats()                    // Dashboard statistics
fraudAPI.getTransactions(params)       // Transaction list
fraudAPI.checkTransaction(data)        // Submit transaction for analysis
fraudAPI.submitFeedback(txnId, data)   // Submit fraud feedback
```

### API Authentication

The API client automatically includes your API key from localStorage:

```typescript
// Store your API key
localStorage.setItem('sentinel_api_key', 'your_api_key_here')
```

## 🎨 Design System

### Colors
- **Primary**: Purple (#8b5cf6) → Pink (#ec4899) gradient
- **Danger**: Red for high-risk transactions
- **Warning**: Yellow for medium-risk
- **Success**: Green for low-risk

### Custom Utilities

```css
.glass              /* Glassmorphism effect */
.glass-dark         /* Darker glass variant */
.text-gradient      /* Purple-pink text gradient */
.glow-effect        /* Glowing shadow */
```

### Animations
- `float` - Gentle floating animation
- `glow` - Pulsing glow effect
- `shimmer` - Loading shimmer

## 🌐 Environment Variables

Create a `.env` file if needed:

```env
VITE_API_BASE_URL=http://localhost:8080
```

## 📱 Mobile Support

The dashboard is fully responsive with:
- Collapsible mobile sidebar
- Touch-friendly interactions
- Optimized 3D graphics for mobile devices
- Responsive grid layouts

## ⚡ Performance

- **Code Splitting**: Routes loaded on demand
- **GPU Acceleration**: CSS transforms use GPU
- **Optimized Renders**: React hooks prevent unnecessary re-renders
- **Lazy Loading**: Components loaded when needed

## 🔧 Configuration

### Tailwind Theme
Customize colors, fonts, and animations in `tailwind.config.js`

### Vite
Configure build options in `vite.config.ts`

### TypeScript
Type checking settings in `tsconfig.json`

## 🐛 Troubleshooting

### CORS Errors
If you see CORS errors, ensure the backend is configured to accept requests from `http://localhost:5173`:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3D Graphics Not Rendering
- Check browser console for WebGL errors
- Ensure your browser supports WebGL 2.0
- Try disabling hardware acceleration if issues persist

### Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📄 License

Part of the Sentinel Nigerian Fraud Detection Platform.
