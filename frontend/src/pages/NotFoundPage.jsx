import React from 'react'
import { Link } from 'react-router-dom'

const NotFoundPage = () => {
  return (
    <div className="auth-page">
      <div className="auth-page__backdrop" />
      <div className="empty-state empty-state--not-found">
        <p className="auth-page__eyebrow">404</p>
        <h1 className="empty-state__title">This page is not in the workspace.</h1>
        <p className="empty-state__text">
          The route could not be found. Head back to the main app shell and keep going.
        </p>
        <Link to="/" className="btn btn-primary">
          Return home
        </Link>
      </div>
    </div>
  )
}

export default NotFoundPage
