import { json } from '@tanstack/start'
import { createAPIFileRoute } from '@tanstack/start/api'

// Updated API route (if you still need it)
export const APIRoute = createAPIFileRoute('/api/moodboards/$moodboardId')({
  POST: async ({ request, params }) => {
    try {
      const formData = await request.formData()

      // Forward the request to your backend
      const response = await fetch(
        `http://localhost:8000/api/v1/moodboards/update_moodboard/${params.moodboardId}`,
        {
          method: 'PUT',
          body: formData,
        },
      )

      const data = await response.json()

      return json(
        {
          success: response.ok,
          message: response.ok
            ? 'Moodboard updated successfully!'
            : 'Failed to update moodboard',
          data: data,
        },
        { status: response.status },
      )
    } catch (error) {
      console.error('Error forwarding moodboard update:', error)
      return json(
        {
          success: false,
          message: 'Failed to update moodboard.',
        },
        { status: 500 },
      )
    }
  },
})
