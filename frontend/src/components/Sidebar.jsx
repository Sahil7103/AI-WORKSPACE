import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const Sidebar = ({ role }) => {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <aside className="w-64 bg-gray-900 text-white">
      <nav className="p-6 space-y-4">
        <Link
          to="/"
          className={`block px-4 py-2 rounded-lg ${
            isActive('/') ? 'bg-blue-600' : 'hover:bg-gray-800'
          }`}
        >
          📊 Dashboard
        </Link>
        
        <Link
          to="/chat"
          className={`block px-4 py-2 rounded-lg ${
            isActive('/chat') ? 'bg-blue-600' : 'hover:bg-gray-800'
          }`}
        >
          💬 Chat
        </Link>
        
        <Link
          to="/documents"
          className={`block px-4 py-2 rounded-lg ${
            isActive('/documents') ? 'bg-blue-600' : 'hover:bg-gray-800'
          }`}
        >
          📄 Documents
        </Link>
        
        {role === 'admin' && (
          <Link
            to="/admin"
            className={`block px-4 py-2 rounded-lg ${
              isActive('/admin') ? 'bg-blue-600' : 'hover:bg-gray-800'
            }`}
          >
            ⚙️ Admin
          </Link>
        )}
      </nav>
    </aside>
  )
}

export default Sidebar
