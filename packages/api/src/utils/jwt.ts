import jwt from 'jsonwebtoken'
import { config } from '../config'

export interface JwtPayload {
  id: string
  email: string
  iat?: number
  exp?: number
}

export class JwtService {
  private static readonly SECRET = config.auth?.jwtSecret || process.env.JWT_SECRET || 'your-secret-key'
  private static readonly EXPIRES_IN = '7d'

  static generateToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
    return jwt.sign(payload, this.SECRET, {
      expiresIn: this.EXPIRES_IN
    })
  }

  static verifyToken(token: string): JwtPayload {
    try {
      return jwt.verify(token, this.SECRET) as JwtPayload
    } catch (error) {
      throw new Error('Invalid token')
    }
  }

  static decodeToken(token: string): JwtPayload | null {
    try {
      return jwt.decode(token) as JwtPayload
    } catch (error) {
      return null
    }
  }
}