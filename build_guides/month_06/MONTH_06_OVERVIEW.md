# MONTH 6: FRONTEND INTEGRATION

## Overview
Month 6 builds the React frontend for the fraud detection dashboard:
- Dashboard UI with real-time fraud monitoring
- Transaction review interface
- Analytics and visualization
- Admin panel UI

**Total for Month 6:** ~4,500 lines of code (TypeScript/React)

---

## Week 1: Dashboard Foundation & Layout
**Days 141-147**

### Files to Build
```
frontend/src/
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.tsx          # 185 lines - Main dashboard
│   │   ├── DashboardLayout.tsx    # 145 lines - Layout component
│   │   └── Sidebar.tsx            # 125 lines - Navigation
│   └── common/
│       ├── Header.tsx             # 95 lines - Header component
│       └── Footer.tsx             # 65 lines - Footer
├── hooks/
│   ├── useAuth.ts                 # 145 lines - Auth hook
│   └── useApi.ts                  # 165 lines - API hook
└── services/
    └── api.ts                     # 215 lines - API client
```

**Total:** 8 files, ~1,140 lines

### Key Features
- Responsive dashboard layout
- Navigation sidebar
- Authentication flow
- API integration layer

### Dependencies
```
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "@tanstack/react-query": "^5.14.2",
    "tailwindcss": "^3.3.6",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.1.1"
  }
}
```

### Components Structure
```tsx
// Dashboard.tsx
export const Dashboard: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard title="Total Transactions" value="12,543" />
        <StatsCard title="Fraud Detected" value="87" trend="-12%" />
        <StatsCard title="Decline Rate" value="6.9%" />
      </div>

      <div className="mt-8">
        <RecentTransactions />
      </div>
    </DashboardLayout>
  );
};
```

---

## Week 2: Transaction Management UI
**Days 148-154**

### Files to Build
```
frontend/src/components/
├── Transactions/
│   ├── TransactionList.tsx        # 285 lines - Transaction table
│   ├── TransactionDetail.tsx      # 245 lines - Detail view
│   ├── TransactionFilters.tsx     # 165 lines - Filter panel
│   └── TransactionActions.tsx     # 135 lines - Bulk actions
├── FraudFlags/
│   ├── FlagsList.tsx              # 195 lines - Flags display
│   └── FlagDetail.tsx             # 145 lines - Flag details
└── common/
    ├── Table.tsx                  # 225 lines - Reusable table
    ├── Pagination.tsx             # 115 lines - Pagination
    └── SearchBar.tsx              # 95 lines - Search
```

**Total:** 9 files, ~1,605 lines

### Key Features
- Sortable, filterable transaction table
- Transaction detail modal
- Fraud flag visualization
- Bulk approve/decline actions
- Real-time updates (WebSocket)

### Dependencies (add)
```
"socket.io-client": "^4.5.4",
"@tanstack/react-table": "^8.10.7",
"date-fns": "^2.30.0"
```

### Example Component
```tsx
// TransactionList.tsx
export const TransactionList: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: fetchTransactions
  });

  return (
    <Table
      data={data?.transactions || []}
      columns={transactionColumns}
      onRowClick={handleTransactionClick}
      isLoading={isLoading}
    />
  );
};
```

---

## Week 3: Analytics & Visualizations
**Days 155-161**

### Files to Build
```
frontend/src/components/
├── Analytics/
│   ├── FraudTrends.tsx            # 265 lines - Trend charts
│   ├── IndustryBreakdown.tsx      # 195 lines - Industry stats
│   ├── RiskDistribution.tsx       # 175 lines - Risk chart
│   └── TopFlags.tsx               # 145 lines - Top flags
├── Charts/
│   ├── LineChart.tsx              # 185 lines - Line chart
│   ├── BarChart.tsx               # 165 lines - Bar chart
│   ├── PieChart.tsx               # 145 lines - Pie chart
│   └── HeatMap.tsx                # 195 lines - Heatmap
└── Reports/
    ├── ReportBuilder.tsx          # 225 lines - Report UI
    └── ReportPreview.tsx          # 165 lines - Preview
```

**Total:** 10 files, ~1,860 lines

### Key Features
- Real-time fraud trend charts
- Industry-wise breakdown
- Risk score distribution
- Interactive visualizations
- Custom report builder

### Dependencies (add)
```
"recharts": "^2.10.3",
"chart.js": "^4.4.1",
"react-chartjs-2": "^5.2.0"
```

### Example Chart
```tsx
// FraudTrends.tsx
export const FraudTrends: React.FC = () => {
  const { data } = useQuery({
    queryKey: ['trends'],
    queryFn: () => api.get('/dashboard/trends?days=30')
  });

  return (
    <LineChart
      data={data?.trends}
      xAxis="date"
      yAxis="declined_transactions"
      color="#EF4444"
    />
  );
};
```

---

## Week 4: Admin Panel & Settings
**Days 162-168**

### Files to Build
```
frontend/src/components/
├── Admin/
│   ├── UserManagement.tsx         # 245 lines - User CRUD
│   ├── RuleConfiguration.tsx      # 285 lines - Rule settings
│   ├── WebhookConfig.tsx          # 215 lines - Webhook setup
│   └── SystemSettings.tsx         # 195 lines - Settings
├── Settings/
│   ├── VerticalSettings.tsx       # 175 lines - Vertical config
│   ├── ThresholdSettings.tsx      # 165 lines - Thresholds
│   └── NotificationSettings.tsx   # 145 lines - Notifications
└── Forms/
    ├── FormBuilder.tsx            # 185 lines - Form builder
    └── FormValidation.ts          # 95 lines - Validation
```

**Total:** 9 files, ~1,705 lines

### Key Features
- User management interface
- Rule enable/disable toggles
- Threshold configuration sliders
- Webhook management UI
- System settings panel

### Example Component
```tsx
// RuleConfiguration.tsx
export const RuleConfiguration: React.FC = () => {
  const { data: rules } = useQuery(['rules'], fetchAllRules);

  const toggleRule = useMutation({
    mutationFn: (ruleId: string) => api.put(`/admin/rules/${ruleId}/toggle`),
    onSuccess: () => queryClient.invalidateQueries(['rules'])
  });

  return (
    <div className="space-y-4">
      {rules?.map(rule => (
        <RuleCard
          key={rule.id}
          rule={rule}
          onToggle={() => toggleRule.mutate(rule.id)}
        />
      ))}
    </div>
  );
};
```

---

## Build & Deployment

### Development
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### Production Build
```bash
npm run build
# Output: frontend/build/
```

### Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENV=development
```

---

## Success Criteria

By end of Month 6:
- ✅ Dashboard showing real-time fraud stats
- ✅ Transaction list with filters
- ✅ Analytics charts and visualizations
- ✅ Admin panel fully functional
- ✅ Responsive design (mobile/tablet/desktop)
- ✅ Real-time updates via WebSocket

---

**End of Month 6 Overview**
