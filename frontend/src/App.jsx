import React, { useState } from 'react'
import { UserProvider, useUser } from './contexts/UserContext'
import { ContactProvider } from './contexts/ContactContext'
import { ThemeProvider } from './components/theme-provider'
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import Dashboard from './pages/Dashboard'
import Contacts from './pages/Contacts'
import Connections from './pages/Connections'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Auth from './pages/Auth'
import './App.css'

function AppContent() {
  const { user, loading, isAuthenticated } = useUser()
  const [currentPage, setCurrentPage] = useState('dashboard')

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando NEXIFY...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Auth />
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'contacts':
        return <Contacts />
      case 'connections':
        return <Connections />
      case 'analytics':
        return <Analytics />
      case 'settings':
        return <Settings />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={user} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="nexify-ui-theme">
      <UserProvider>
        <ContactProvider>
          <AppContent />
        </ContactProvider>
      </UserProvider>
    </ThemeProvider>
  )
}

export default App

