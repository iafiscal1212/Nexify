import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  LayoutDashboard, 
  Users, 
  Network, 
  BarChart3, 
  Settings,
  Zap
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Contactos',
    href: '/contacts',
    icon: Users,
  },
  {
    name: 'Conexiones',
    href: '/connections',
    icon: Network,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'Configuración',
    href: '/settings',
    icon: Settings,
  },
]

export default function Sidebar({ open, setOpen }) {
  const location = useLocation()

  return (
    <>
      {/* Overlay para móvil */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-200 transition-all duration-300",
          open ? "w-64" : "w-16",
          "lg:translate-x-0",
          !open && "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-center h-16 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            {open && (
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                NEXIFY
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon

              return (
                <Link key={item.name} to={item.href}>
                  <Button
                    variant={isActive ? "default" : "ghost"}
                    className={cn(
                      "w-full justify-start",
                      !open && "px-2",
                      isActive && "bg-blue-50 text-blue-700 hover:bg-blue-100"
                    )}
                  >
                    <Icon className={cn("h-5 w-5", open && "mr-3")} />
                    {open && <span>{item.name}</span>}
                  </Button>
                </Link>
              )
            })}
          </nav>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          {open ? (
            <div className="text-xs text-gray-500 text-center">
              <p>NEXIFY v1.0</p>
              <p>IA para conexiones</p>
            </div>
          ) : (
            <div className="w-8 h-8 bg-gray-100 rounded-full mx-auto"></div>
          )}
        </div>
      </div>
    </>
  )
}

