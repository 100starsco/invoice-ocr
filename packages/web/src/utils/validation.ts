export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean;
  message?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export class Validator {
  static validate(value: any, rules: ValidationRule[]): ValidationResult {
    const errors: string[] = [];

    for (const rule of rules) {
      if (rule.required && !value) {
        errors.push(rule.message || 'This field is required');
        continue;
      }

      if (value && rule.minLength && value.length < rule.minLength) {
        errors.push(rule.message || `Minimum length is ${rule.minLength}`);
      }

      if (value && rule.maxLength && value.length > rule.maxLength) {
        errors.push(rule.message || `Maximum length is ${rule.maxLength}`);
      }

      if (value && rule.pattern && !rule.pattern.test(value)) {
        errors.push(rule.message || 'Invalid format');
      }

      if (value && rule.custom && !rule.custom(value)) {
        errors.push(rule.message || 'Validation failed');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  static validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  static validatePhone(phone: string): boolean {
    const phoneRegex = /^[0-9]{10}$/;
    return phoneRegex.test(phone.replace(/[^0-9]/g, ''));
  }

  static validateDate(date: string): boolean {
    const dateObj = new Date(date);
    return dateObj instanceof Date && !isNaN(dateObj.getTime());
  }

  static validateNumber(value: any, min?: number, max?: number): boolean {
    const num = Number(value);
    if (isNaN(num)) return false;
    if (min !== undefined && num < min) return false;
    if (max !== undefined && num > max) return false;
    return true;
  }

  static validateThaiId(id: string): boolean {
    if (!/^\d{13}$/.test(id)) return false;

    let sum = 0;
    for (let i = 0; i < 12; i++) {
      sum += parseInt(id.charAt(i)) * (13 - i);
    }
    const checkDigit = (11 - (sum % 11)) % 10;
    return checkDigit === parseInt(id.charAt(12));
  }

  static validateInvoiceNumber(invoiceNo: string): boolean {
    return /^[A-Z0-9\-\/]+$/i.test(invoiceNo);
  }

  static sanitizeInput(input: string): string {
    return input.trim().replace(/<[^>]*>?/gm, '');
  }
}

export const validator = new Validator();