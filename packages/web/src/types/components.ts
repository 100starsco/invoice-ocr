export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  type?: 'button' | 'submit' | 'reset';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: any;
  iconPosition?: 'left' | 'right';
}

export interface InputProps {
  modelValue: string | number;
  type?: string;
  label?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'bordered' | 'ghost';
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  icon?: any;
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  icon?: any;
}

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  formatter?: (value: any) => string;
}

export interface ModalProps {
  modelValue: boolean;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closable?: boolean;
  closeOnEsc?: boolean;
  closeOnBackdrop?: boolean;
  persistent?: boolean;
}

export interface ToastProps {
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
  position?: 'top' | 'bottom' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  closable?: boolean;
}

export interface TabItem {
  key: string;
  label: string;
  icon?: any;
  disabled?: boolean;
  badge?: string | number;
}

export interface MenuItem {
  key: string;
  label: string;
  icon?: any;
  to?: string;
  href?: string;
  disabled?: boolean;
  children?: MenuItem[];
  badge?: string | number;
}

export interface BreadcrumbItem {
  label: string;
  to?: string;
  href?: string;
  icon?: any;
}

export interface StepItem {
  key: string;
  label: string;
  description?: string;
  icon?: any;
  status?: 'pending' | 'active' | 'completed' | 'error';
}

export interface DropdownItem {
  key: string;
  label: string;
  icon?: any;
  disabled?: boolean;
  divider?: boolean;
  danger?: boolean;
  onClick?: () => void;
}

export interface FormField {
  name: string;
  label?: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'checkbox' | 'radio' | 'textarea' | 'file';
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  options?: SelectOption[];
  validation?: any[];
  hint?: string;
  icon?: any;
}