# Sprint 04: Web UI Shell

**Phase:** 1 - Foundation
**Focus:** Next.js frontend application shell with routing and auth integration
**Dependencies:** Sprint 02 (Auth), Sprint 03 (API)

---

## Testable Deliverable

**Human Test:**
1. Navigate to the app URL
2. Redirected to login page if not authenticated
3. Login with credentials
4. Land on dashboard
5. Navigate between sections (memories, conversations, settings)
6. View connected services in settings
7. Logout successfully
8. Protected routes redirect to login

**Manual Testing:**
```
1. Open http://localhost:3000
2. See login form
3. Enter credentials and submit
4. See dashboard with navigation sidebar
5. Click "Memories" in sidebar → see memories page
6. Click "Conversations" → see conversations page
7. Click "Settings" → see settings with profile and integrations sections
8. Click "Logout" → return to login page
9. Try direct URL /dashboard → redirected to login
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_007 | Web-based application interface | 17 |
| REQ_008 | Desktop browser compatible | 17 |

### Implementation Requirements

**Group 014 - UI Components (10 requirements)**
- REQ_007.2.1: Implement responsive web application layout
- REQ_007.2.2: Create navigation system
- REQ_008.2.1: Desktop browser compatibility
- REQ_008.2.2: Responsive design for various screen sizes

---

## Tech Stack

```
Framework: Next.js 14 (App Router)
Styling: Tailwind CSS + shadcn/ui
State: Zustand for client state
API: React Query (TanStack Query) for server state
Auth: httpOnly cookies for tokens (secure)
Icons: Lucide React
```

---

## Application Structure

```
├── App Layout
│   ├── Auth Pages (no sidebar)
│   │   ├── /login
│   │   └── /register
│   │
│   └── Dashboard Layout (with sidebar)
│       ├── /dashboard (overview)
│       ├── /dashboard/memories
│       ├── /dashboard/conversations
│       ├── /dashboard/tasks
│       ├── /dashboard/search
│       └── /dashboard/settings
│           ├── Profile
│           ├── Preferences
│           └── Integrations (Connected Services)
```

---

## UI Components

### Layout Components
```
- AppShell: Main layout wrapper
- Sidebar: Navigation sidebar (collapsible)
- TopBar: User menu, notifications
- PageHeader: Page title with actions
```

### Common Components
```
- Button, Input, Card, Modal (from shadcn/ui)
- Avatar: User avatar display
- LoadingSpinner: Loading states
- EmptyState: No data placeholder
- ErrorBoundary: Error handling
```

### Auth Components
```
- LoginForm: Email/password login
- RegisterForm: Account registration
- AuthGuard: Protected route wrapper
```

### Settings Components
```
- ProfileForm: Edit user profile
- PreferencesForm: App preferences (theme, language)
- IntegrationsPanel: Connected services display
```

---

## API Integration

### Auth Flow (httpOnly Cookies)
```typescript
// Token storage: httpOnly cookies (set by backend)
// Frontend never sees raw tokens - more secure

// Login
const login = async (email: string, password: string) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include', // Important for cookies
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return response.json();
};

// Get current user
const getCurrentUser = async () => {
  const response = await fetch('/api/auth/me', {
    credentials: 'include'
  });
  if (!response.ok) throw new Error('Not authenticated');
  return response.json();
};

// Logout
const logout = async () => {
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
};
```

### API Client
```typescript
// lib/api-client.ts
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      credentials: 'include', // Always include cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Redirect to login
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Request failed');
    }

    return response.json();
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
```

---

## Tasks

### Project Setup
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Set up project folder structure
- [ ] Configure environment variables

### Auth Integration
- [ ] Create login page with form
- [ ] Create register page with form
- [ ] Implement AuthContext provider
- [ ] Create AuthGuard component for protected routes
- [ ] Handle auth redirects
- [ ] Configure httpOnly cookie handling

### Layout System
- [ ] Create AppShell component
- [ ] Build responsive Sidebar with navigation
- [ ] Build TopBar with user menu
- [ ] Implement collapsible sidebar (mobile responsive)
- [ ] Create PageHeader component

### Core Pages (Placeholders)
- [ ] Dashboard overview page
- [ ] Memories page
- [ ] Conversations page
- [ ] Tasks page
- [ ] Search page

### Settings Pages
- [ ] Settings layout with tabs/sections
- [ ] Profile settings page
- [ ] Preferences settings page
- [ ] Integrations settings page (Connected Services)

### API Client
- [ ] Create API client with cookie handling
- [ ] Set up React Query provider
- [ ] Create auth hooks (useAuth, useCurrentUser)
- [ ] Create settings hooks (useProfile, usePreferences, useIntegrations)

### State Management
- [ ] Set up Zustand store
- [ ] User state management
- [ ] UI state (sidebar open/closed, theme)

### Common Components
- [ ] Loading spinner
- [ ] Empty state component
- [ ] Error boundary
- [ ] Toast notifications

---

## Acceptance Criteria

1. Login/register pages functional
2. Authentication flow works with httpOnly cookies
3. Protected routes redirect to login
4. Dashboard layout renders with sidebar
5. Navigation between pages works
6. Settings pages accessible
7. Integrations section shows in settings (Connect/Disconnect buttons)
8. Logout clears session
9. Mobile-responsive sidebar
10. Dark/light theme support

---

## Files to Create

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── page.tsx              # Overview
│   │   │   ├── layout.tsx            # Dashboard layout
│   │   │   ├── memories/
│   │   │   │   └── page.tsx
│   │   │   ├── conversations/
│   │   │   │   └── page.tsx
│   │   │   ├── tasks/
│   │   │   │   └── page.tsx
│   │   │   ├── search/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       ├── page.tsx          # Profile settings
│   │   │       ├── preferences/
│   │   │       │   └── page.tsx
│   │   │       └── integrations/
│   │   │           └── page.tsx
│   │   │
│   │   ├── layout.tsx                # Root layout
│   │   ├── page.tsx                  # Landing/redirect
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── AuthGuard.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── PageHeader.tsx
│   │   │
│   │   ├── settings/
│   │   │   ├── ProfileForm.tsx
│   │   │   ├── PreferencesForm.tsx
│   │   │   └── IntegrationsPanel.tsx
│   │   │
│   │   └── ui/                       # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── card.tsx
│   │       └── ...
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useCurrentUser.ts
│   │   ├── usePreferences.ts
│   │   └── useIntegrations.ts
│   │
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── utils.ts
│   │
│   ├── providers/
│   │   ├── AuthProvider.tsx
│   │   └── QueryProvider.tsx
│   │
│   ├── stores/
│   │   └── ui-store.ts
│   │
│   └── types/
│       ├── user.ts
│       ├── integration.ts
│       └── api.ts
│
├── tailwind.config.ts
├── next.config.js
├── package.json
└── .env.local
```

---

## Key Component Implementations

### AuthGuard
```typescript
// components/auth/AuthGuard.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading, error } = useCurrentUser();

  useEffect(() => {
    if (!isLoading && (error || !user)) {
      router.replace('/login');
    }
  }, [user, isLoading, error, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
```

### Sidebar
```typescript
// components/layout/Sidebar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Brain,
  MessageSquare,
  CheckSquare,
  Search,
  Settings,
  ChevronLeft
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/ui-store';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Memories', href: '/dashboard/memories', icon: Brain },
  { name: 'Conversations', href: '/dashboard/conversations', icon: MessageSquare },
  { name: 'Tasks', href: '/dashboard/tasks', icon: CheckSquare },
  { name: 'Search', href: '/dashboard/search', icon: Search },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-gray-900 text-white transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4">
        {sidebarOpen && <span className="text-xl font-bold">Tanka AI</span>}
        <button
          onClick={toggleSidebar}
          className="p-2 rounded hover:bg-gray-800"
        >
          <ChevronLeft className={cn('h-5 w-5 transition-transform', !sidebarOpen && 'rotate-180')} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 rounded-lg transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {sidebarOpen && <span className="ml-3">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Settings link at bottom */}
      <div className="p-2 border-t border-gray-800">
        <Link
          href="/dashboard/settings"
          className={cn(
            'flex items-center px-3 py-2 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white',
            pathname.startsWith('/dashboard/settings') && 'bg-gray-800 text-white'
          )}
        >
          <Settings className="h-5 w-5 flex-shrink-0" />
          {sidebarOpen && <span className="ml-3">Settings</span>}
        </Link>
      </div>
    </aside>
  );
}
```

### Integrations Panel (Connected Services)
```typescript
// components/settings/IntegrationsPanel.tsx
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mail, Calendar, HardDrive } from 'lucide-react';

interface Integration {
  id: string;
  provider: string;
  status: 'active' | 'expired' | 'disconnected';
  provider_email: string;
  scopes: string[];
  connected_at: string;
  last_sync_at: string;
}

const providerConfig = {
  google: {
    name: 'Google',
    icon: Mail,
    color: 'text-red-500',
    services: ['Gmail', 'Calendar', 'Drive']
  },
  microsoft: {
    name: 'Microsoft 365',
    icon: Calendar,
    color: 'text-blue-500',
    services: ['Outlook', 'Calendar', 'OneDrive']
  }
};

export function IntegrationsPanel() {
  const queryClient = useQueryClient();

  const { data: integrations, isLoading } = useQuery<Integration[]>({
    queryKey: ['integrations'],
    queryFn: () => api.get('/api/v1/integrations'),
  });

  const disconnectMutation = useMutation({
    mutationFn: (integrationId: string) =>
      api.delete(`/api/v1/integrations/${integrationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const handleConnect = (provider: string) => {
    // Redirect to OAuth flow
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/integrations/${provider}/connect`;
  };

  if (isLoading) {
    return <div>Loading integrations...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Connected Services</h2>
        <p className="text-gray-600">
          Connect your accounts to sync emails, calendars, and files.
        </p>
      </div>

      <div className="grid gap-4">
        {Object.entries(providerConfig).map(([key, config]) => {
          const integration = integrations?.find(i => i.provider === key);
          const Icon = config.icon;

          return (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Icon className={`h-8 w-8 ${config.color}`} />
                  <div>
                    <CardTitle>{config.name}</CardTitle>
                    <CardDescription>
                      {config.services.join(', ')}
                    </CardDescription>
                  </div>
                </div>

                {integration ? (
                  <div className="flex items-center space-x-2">
                    <Badge variant={integration.status === 'active' ? 'default' : 'destructive'}>
                      {integration.status}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => disconnectMutation.mutate(integration.id)}
                      disabled={disconnectMutation.isPending}
                    >
                      Disconnect
                    </Button>
                  </div>
                ) : (
                  <Button onClick={() => handleConnect(key)}>
                    Connect
                  </Button>
                )}
              </CardHeader>

              {integration && (
                <CardContent>
                  <p className="text-sm text-gray-500">
                    Connected as {integration.provider_email}
                  </p>
                  <p className="text-xs text-gray-400">
                    Last synced: {integration.last_sync_at
                      ? new Date(integration.last_sync_at).toLocaleString()
                      : 'Never'}
                  </p>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
```

### Dashboard Layout
```typescript
// app/dashboard/layout.tsx
import { AuthGuard } from '@/components/auth/AuthGuard';
import { AppShell } from '@/components/layout/AppShell';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
```

---

## State Management

```typescript
// stores/ui-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'system',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'ui-storage',
    }
  )
);
```

---

## Hooks

### useCurrentUser
```typescript
// hooks/useCurrentUser.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

interface User {
  id: string;
  email: string;
  display_name: string;
  first_name: string;
  last_name: string;
  avatar_url: string;
}

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: () => api.get('/api/auth/me'),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

### useIntegrations
```typescript
// hooks/useIntegrations.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

export function useIntegrations() {
  return useQuery({
    queryKey: ['integrations'],
    queryFn: () => api.get('/api/v1/integrations'),
  });
}
```

---

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Tanka AI
```

---

## Related Requirement Groups

- Group 014: Semantic: UI Components
- Group 001: Implementation (frontend)
- Group 019: Semantic: User Interface
- UI Components domain
