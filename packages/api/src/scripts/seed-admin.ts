import 'dotenv/config'
import { AdminAuthService } from '../services/admin-auth'

async function seedAdminUser() {
  try {
    const email = process.env.ADMIN_EMAIL || 'admin@example.com'
    const password = process.env.ADMIN_PASSWORD || 'admin123'
    const name = process.env.ADMIN_NAME || 'System Administrator'

    console.log('Creating admin user...')
    console.log(`Email: ${email}`)
    console.log(`Name: ${name}`)

    const adminUser = await AdminAuthService.createAdminUser({
      email,
      password,
      name
    })

    console.log('✅ Admin user created successfully!')
    console.log(`ID: ${adminUser.id}`)
    console.log(`Email: ${adminUser.email}`)
    console.log(`Name: ${adminUser.name}`)
    console.log(`Active: ${adminUser.isActive}`)
    console.log(`Created: ${adminUser.createdAt}`)

    console.log('\n🔐 Login credentials:')
    console.log(`Email: ${email}`)
    console.log(`Password: ${password}`)
    console.log('\n⚠️  Please change the default password after first login!')

  } catch (error) {
    if (error instanceof Error) {
      if (error.message === 'Admin user already exists') {
        console.log('ℹ️  Admin user already exists')
      } else {
        console.error('❌ Error creating admin user:', error.message)
      }
    } else {
      console.error('❌ Unknown error:', error)
    }
    process.exit(1)
  }
}

seedAdminUser()