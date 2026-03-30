import React, { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { authAPI } from '../services/api'

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setIsAuthenticated(false)
        return
      }

      try {
        await authAPI.getMe()
        setIsAuthenticated(true)
      } catch (error) {
        localStorage.removeItem('auth_token')
        setIsAuthenticated(false)
      }
    }

    checkAuth()
  }, [])

  if (isAuthenticated === null) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />
  }

  return children
}

export default ProtectedRoute
