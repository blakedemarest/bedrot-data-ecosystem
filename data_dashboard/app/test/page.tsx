'use client'

export default function TestPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Dashboard Test Page</h1>
      <p>If you can see this, the frontend is working!</p>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mt-4">
        <h2 className="text-lg font-semibold">Basic Component Test</h2>
        <p className="text-gray-600 dark:text-gray-300">This is a simple test.</p>
      </div>
    </div>
  )
}