import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import { config } from '../config'
import * as schema from './schema'

// Create PostgreSQL connection
const client = postgres(config.database.postgresql.url, {
  max: 10,
  idle_timeout: 20,
  connect_timeout: 10,
})

// Create Drizzle database instance
export const db = drizzle(client, { schema })

// Helper function to close database connection
export const closeDB = async () => {
  await client.end()
}

// Export schema for external use
export { schema }
export * from './schema'