import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <h1 className="text-4xl font-bold text-green-800 mb-2">404</h1>
      <p className="text-gray-600 mb-6">Page not found.</p>
      <Link to="/login" className="text-green-700 font-medium underline">Go back home</Link>
    </div>
  )
}