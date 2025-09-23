import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { db } from '../db'
import { adminUsers } from '../db/schema'
import { JwtService } from '../utils/jwt'

export interface LoginCredentials {
  email: string
  password: string
}

export interface AdminUser {
  id: string
  email: string
  name: string
  isActive: boolean
  createdAt: Date
  updatedAt: Date
}

export interface LoginResponse {
  user: AdminUser
  token: string
}

export class AdminAuthService {
  static async hashPassword(password: string): Promise<string> {
    const saltRounds = 12
    return bcrypt.hash(password, saltRounds)
  }

  static async verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
    return bcrypt.compare(password, hashedPassword)
  }

  static async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const { email, password } = credentials

    // Find admin user by email
    const [adminUser] = await db
      .select()
      .from(adminUsers)
      .where(eq(adminUsers.email, email.toLowerCase()))
      .limit(1)

    if (!adminUser) {
      throw new Error('Invalid credentials')
    }

    if (!adminUser.isActive) {
      throw new Error('Account is disabled')
    }

    // Verify password
    const isValidPassword = await this.verifyPassword(password, adminUser.passwordHash)
    if (!isValidPassword) {
      throw new Error('Invalid credentials')
    }

    // Generate JWT token
    const token = JwtService.generateToken({
      id: adminUser.id,
      email: adminUser.email
    })

    // Return user data (without password hash) and token
    const userResponse: AdminUser = {
      id: adminUser.id,
      email: adminUser.email,
      name: adminUser.name,
      isActive: adminUser.isActive,
      createdAt: adminUser.createdAt,
      updatedAt: adminUser.updatedAt
    }

    return {
      user: userResponse,
      token
    }
  }

  static async verifyToken(token: string): Promise<AdminUser> {
    try {
      const payload = JwtService.verifyToken(token)

      // Find admin user by ID from token
      const [adminUser] = await db
        .select()
        .from(adminUsers)
        .where(eq(adminUsers.id, payload.id))
        .limit(1)

      if (!adminUser || !adminUser.isActive) {
        throw new Error('Invalid token')
      }

      return {
        id: adminUser.id,
        email: adminUser.email,
        name: adminUser.name,
        isActive: adminUser.isActive,
        createdAt: adminUser.createdAt,
        updatedAt: adminUser.updatedAt
      }
    } catch (error) {
      throw new Error('Invalid token')
    }
  }

  static async createAdminUser(userData: {
    email: string
    password: string
    name: string
  }): Promise<AdminUser> {
    const { email, password, name } = userData

    // Check if admin already exists
    const [existingAdmin] = await db
      .select()
      .from(adminUsers)
      .where(eq(adminUsers.email, email.toLowerCase()))
      .limit(1)

    if (existingAdmin) {
      throw new Error('Admin user already exists')
    }

    // Hash password
    const passwordHash = await this.hashPassword(password)

    // Create admin user
    const [newAdmin] = await db
      .insert(adminUsers)
      .values({
        email: email.toLowerCase(),
        passwordHash,
        name,
        isActive: true
      })
      .returning()

    return {
      id: newAdmin.id,
      email: newAdmin.email,
      name: newAdmin.name,
      isActive: newAdmin.isActive,
      createdAt: newAdmin.createdAt,
      updatedAt: newAdmin.updatedAt
    }
  }
}