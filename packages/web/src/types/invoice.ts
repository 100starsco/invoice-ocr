export interface Invoice {
  id: string;
  invoiceNumber: string;
  vendor: VendorInfo;
  customer?: CustomerInfo;
  date: Date;
  dueDate?: Date;
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
  status: InvoiceStatus;
  category?: InvoiceCategory;
  notes?: string;
  attachments?: Attachment[];
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface VendorInfo {
  name: string;
  address?: string;
  taxId?: string;
  phone?: string;
  email?: string;
}

export interface CustomerInfo {
  name: string;
  address?: string;
  taxId?: string;
  phone?: string;
  email?: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  amount: number;
  tax?: number;
  discount?: number;
}

export interface Attachment {
  id: string;
  filename: string;
  url: string;
  mimeType: string;
  size: number;
  uploadedAt: Date;
}

export enum InvoiceStatus {
  DRAFT = 'DRAFT',
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum InvoiceCategory {
  FOOD = 'FOOD',
  TRANSPORT = 'TRANSPORT',
  UTILITIES = 'UTILITIES',
  OFFICE = 'OFFICE',
  ENTERTAINMENT = 'ENTERTAINMENT',
  HEALTHCARE = 'HEALTHCARE',
  SHOPPING = 'SHOPPING',
  OTHER = 'OTHER',
}

export interface InvoiceFilter {
  status?: InvoiceStatus;
  category?: InvoiceCategory;
  dateFrom?: Date;
  dateTo?: Date;
  vendor?: string;
  minAmount?: number;
  maxAmount?: number;
}

export interface InvoiceSummary {
  totalInvoices: number;
  totalAmount: number;
  averageAmount: number;
  byCategory: Record<InvoiceCategory, number>;
  byStatus: Record<InvoiceStatus, number>;
  byMonth: Array<{ month: string; amount: number; count: number }>;
}