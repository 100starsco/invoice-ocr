import { Hono } from 'hono'
import { swaggerUI } from '@hono/swagger-ui'

const docs = new Hono()

// Static OpenAPI specification
const openApiSpec = {
  openapi: '3.0.0',
  info: {
    title: 'Invoice OCR Admin API',
    version: '1.0.0',
    description: 'API documentation for Invoice OCR system admin endpoints. These endpoints require admin authentication via JWT Bearer token.'
  },
  servers: [
    {
      url: 'http://localhost:3000/api/admin',
      description: 'Local development server'
    }
  ],
  components: {
    securitySchemes: {
      Bearer: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: 'JWT Bearer token for admin authentication'
      }
    },
    schemas: {
      Error: {
        type: 'object',
        properties: {
          error: {
            type: 'string'
          }
        }
      },
      SuccessResponse: {
        type: 'object',
        properties: {
          success: {
            type: 'boolean',
            enum: [true]
          },
          data: {
            type: 'object'
          }
        }
      },
      LineUser: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            description: 'User UUID'
          },
          userId: {
            type: 'string',
            description: 'LINE User ID'
          },
          displayName: {
            type: 'string',
            nullable: true,
            description: 'User display name'
          },
          pictureUrl: {
            type: 'string',
            nullable: true,
            description: 'User profile picture URL'
          },
          statusMessage: {
            type: 'string',
            nullable: true,
            description: 'User status message'
          },
          language: {
            type: 'string',
            nullable: true,
            description: 'User language preference'
          },
          isFollowing: {
            type: 'boolean',
            description: 'Whether user is following the bot'
          },
          isBlocked: {
            type: 'boolean',
            description: 'Whether user is blocked'
          },
          profileLastUpdated: {
            type: 'string',
            nullable: true,
            description: 'Last profile update timestamp'
          },
          firstSeenAt: {
            type: 'string',
            description: 'First seen timestamp'
          },
          lastSeenAt: {
            type: 'string',
            description: 'Last seen timestamp'
          },
          lastMessageAt: {
            type: 'string',
            nullable: true,
            description: 'Last message timestamp'
          },
          createdAt: {
            type: 'string',
            description: 'Created timestamp'
          },
          updatedAt: {
            type: 'string',
            description: 'Updated timestamp'
          }
        }
      },
      Message: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            description: 'Message UUID'
          },
          messageId: {
            type: 'string',
            description: 'LINE Message ID'
          },
          messageType: {
            type: 'string',
            description: 'Message type (text, image, etc.)'
          },
          content: {
            type: 'object',
            description: 'Message content'
          },
          userId: {
            type: 'string',
            description: 'LINE User ID'
          },
          sentAt: {
            type: 'string',
            description: 'Message sent timestamp'
          },
          receivedAt: {
            type: 'string',
            description: 'Message received timestamp'
          },
          responded: {
            type: 'boolean',
            description: 'Whether message has been responded to'
          },
          user: {
            type: 'object',
            nullable: true,
            properties: {
              displayName: {
                type: 'string',
                nullable: true
              },
              pictureUrl: {
                type: 'string',
                nullable: true
              }
            },
            description: 'User information'
          }
        }
      }
    }
  },
  paths: {
    '/login': {
      post: {
        tags: ['Authentication'],
        summary: 'Admin login',
        description: 'Authenticate admin user and receive JWT token',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  email: {
                    type: 'string',
                    format: 'email',
                    description: 'Admin email address'
                  },
                  password: {
                    type: 'string',
                    minLength: 1,
                    description: 'Admin password'
                  }
                },
                required: ['email', 'password']
              }
            }
          }
        },
        responses: {
          '200': {
            description: 'Login successful',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: {
                      type: 'boolean',
                      enum: [true]
                    },
                    data: {
                      type: 'object',
                      properties: {
                        user: {
                          type: 'object',
                          properties: {
                            id: { type: 'string' },
                            email: { type: 'string' },
                            name: { type: 'string' },
                            isActive: { type: 'boolean' },
                            createdAt: { type: 'string' },
                            updatedAt: { type: 'string' }
                          }
                        },
                        token: { type: 'string' }
                      }
                    }
                  }
                }
              }
            }
          },
          '401': {
            description: 'Invalid credentials',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' }
              }
            }
          }
        }
      }
    },
    '/users': {
      get: {
        tags: ['User Management'],
        summary: 'List LINE users',
        description: 'Get paginated list of LINE users with filtering and sorting options',
        security: [{ Bearer: [] }],
        parameters: [
          {
            name: 'limit',
            in: 'query',
            description: 'Number of items per page (max 100)',
            schema: { type: 'string', default: '20' }
          },
          {
            name: 'offset',
            in: 'query',
            description: 'Number of items to skip',
            schema: { type: 'string', default: '0' }
          },
          {
            name: 'search',
            in: 'query',
            description: 'Search users by display name',
            schema: { type: 'string' }
          },
          {
            name: 'isFollowing',
            in: 'query',
            description: 'Filter by following status (true/false)',
            schema: { type: 'string' }
          },
          {
            name: 'sortBy',
            in: 'query',
            description: 'Field to sort by',
            schema: {
              type: 'string',
              enum: ['displayName', 'lastSeenAt', 'firstSeenAt', 'lastMessageAt']
            }
          },
          {
            name: 'sortOrder',
            in: 'query',
            description: 'Sort order',
            schema: {
              type: 'string',
              enum: ['asc', 'desc']
            }
          }
        ],
        responses: {
          '200': {
            description: 'Users retrieved successfully',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [true] },
                    data: {
                      type: 'object',
                      properties: {
                        users: {
                          type: 'array',
                          items: { $ref: '#/components/schemas/LineUser' }
                        },
                        total: { type: 'number' },
                        limit: { type: 'number' },
                        offset: { type: 'number' },
                        hasMore: { type: 'boolean' }
                      }
                    }
                  }
                }
              }
            }
          },
          '500': {
            description: 'Server error',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' }
              }
            }
          }
        }
      }
    },
    '/users/{userId}': {
      get: {
        tags: ['User Management'],
        summary: 'Get user details',
        description: 'Get detailed information about a specific user including message count',
        security: [{ Bearer: [] }],
        parameters: [
          {
            name: 'userId',
            in: 'path',
            required: true,
            description: 'LINE User ID',
            schema: { type: 'string', minLength: 1 }
          }
        ],
        responses: {
          '200': {
            description: 'User details retrieved',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [true] },
                    data: {
                      type: 'object',
                      properties: {
                        user: {
                          allOf: [
                            { $ref: '#/components/schemas/LineUser' },
                            {
                              type: 'object',
                              properties: {
                                messageCount: {
                                  type: 'number',
                                  description: 'Total message count for this user'
                                }
                              }
                            }
                          ]
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          '404': {
            description: 'User not found',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' }
              }
            }
          }
        }
      }
    },
    '/messages': {
      get: {
        tags: ['Message Management'],
        summary: 'List messages',
        description: 'Get paginated list of messages with filtering options',
        security: [{ Bearer: [] }],
        parameters: [
          {
            name: 'limit',
            in: 'query',
            description: 'Number of items per page (max 100)',
            schema: { type: 'string', default: '20' }
          },
          {
            name: 'offset',
            in: 'query',
            description: 'Number of items to skip',
            schema: { type: 'string', default: '0' }
          },
          {
            name: 'userId',
            in: 'query',
            description: 'Filter by user ID',
            schema: { type: 'string' }
          },
          {
            name: 'messageType',
            in: 'query',
            description: 'Filter by message type',
            schema: { type: 'string' }
          },
          {
            name: 'dateFrom',
            in: 'query',
            description: 'Filter messages from date (ISO string)',
            schema: { type: 'string' }
          },
          {
            name: 'dateTo',
            in: 'query',
            description: 'Filter messages to date (ISO string)',
            schema: { type: 'string' }
          },
          {
            name: 'sortBy',
            in: 'query',
            description: 'Field to sort by',
            schema: {
              type: 'string',
              enum: ['sentAt', 'receivedAt', 'createdAt']
            }
          },
          {
            name: 'sortOrder',
            in: 'query',
            description: 'Sort order',
            schema: {
              type: 'string',
              enum: ['asc', 'desc']
            }
          }
        ],
        responses: {
          '200': {
            description: 'Messages retrieved successfully',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [true] },
                    data: {
                      type: 'object',
                      properties: {
                        messages: {
                          type: 'array',
                          items: { $ref: '#/components/schemas/Message' }
                        },
                        total: { type: 'number' },
                        limit: { type: 'number' },
                        offset: { type: 'number' },
                        hasMore: { type: 'boolean' }
                      }
                    }
                  }
                }
              }
            }
          },
          '500': {
            description: 'Server error',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' }
              }
            }
          }
        }
      }
    }
  }
}

// Swagger UI endpoint
docs.get('/ui', swaggerUI({ url: '/api/docs/openapi.json' }))

// OpenAPI JSON endpoint
docs.get('/openapi.json', (c) => {
  return c.json(openApiSpec)
})

export { docs }