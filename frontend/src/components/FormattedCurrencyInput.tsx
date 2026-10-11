import React, { useState, useEffect, useRef } from 'react';
import { formatNumberCOP, parseFormattedNumber } from '../utils/formatters';

interface FormattedCurrencyInputProps {
  id?: string;
  name: string;
  value: number | string | undefined | null;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  required?: boolean;
}

export const FormattedCurrencyInput: React.FC<FormattedCurrencyInputProps> = ({
  id,
  name,
  value,
  onChange,
  placeholder = '',
  className = '',
  disabled = false,
  required = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  // Inicializar el valor visual con separadores de miles
  const [displayValue, setDisplayValue] = useState<string>(() => {
    if (value === undefined || value === null || value === '') {
      return '';
    }
    if (value === 0 || value === '0') {
      return '0';
    }
    return formatNumberCOP(value);
  });

  // Sincronizar cuando el prop value cambia externamente (ej. auto-calculos, carga de ejemplo, reset)
  useEffect(() => {
    if (value === undefined || value === null || value === '') {
      if (displayValue !== '') {
        setDisplayValue('');
      }
      return;
    }
    const currentNumeric = parseFormattedNumber(displayValue);
    const incomingNumeric = typeof value === 'number' ? value : parseFormattedNumber(value);

    // Solo actualizar si el valor externo difiere del numero actual en pantalla
    if (incomingNumeric !== currentNumeric) {
      if (incomingNumeric === null) {
        setDisplayValue('');
      } else {
        setDisplayValue(formatNumberCOP(incomingNumeric));
      }
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target;
    const rawInput = input.value;
    const cursorPosition = input.selectionStart ?? rawInput.length;

    // Contar cuantos digitos hay antes del cursor antes de formatear
    const digitsBeforeCursor = rawInput.slice(0, cursorPosition).replace(/[^\d]/g, '').length;

    // Extraer digitos puros
    const cleanedDigits = rawInput.replace(/[^\d]/g, '');

    if (cleanedDigits === '') {
      setDisplayValue('');
      const syntheticEvent = {
        ...e,
        target: {
          ...e.target,
          name,
          value: '',
          type: 'text',
        },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      onChange(syntheticEvent);
      return;
    }

    const numericValue = parseInt(cleanedDigits, 10);
    if (isNaN(numericValue)) return;

    // Formatear con separador de miles colombiano
    const formatted = formatNumberCOP(numericValue);

    // Calcular la nueva posicion del cursor manteniendo coherencia
    let newCursorPos = 0;
    let digitCount = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (/\d/.test(formatted[i])) {
        digitCount++;
      }
      if (digitCount === digitsBeforeCursor) {
        newCursorPos = i + 1;
        break;
      }
    }
    if (digitsBeforeCursor === 0) newCursorPos = 0;
    if (digitCount < digitsBeforeCursor) newCursorPos = formatted.length;

    setDisplayValue(formatted);

    // Notificar al estado padre con el valor numerico puro como string para type=number
    const syntheticEvent = {
      ...e,
      target: {
        ...e.target,
        name,
        value: numericValue.toString(),
        type: 'number',
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;
    onChange(syntheticEvent);

    // Restaurar cursor en la posicion calculada
    requestAnimationFrame(() => {
      if (inputRef.current) {
        inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
      }
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    const start = input.selectionStart;
    const end = input.selectionEnd;

    if (start === null || end === null || start !== end) {
      return;
    }

    // Caso 1: Backspace cuando el caracter a la izquierda es un punto de miles
    if (e.key === 'Backspace' && start > 0 && input.value[start - 1] === '.') {
      e.preventDefault();
      // Eliminar el digito previo al punto (start - 2)
      const before = input.value.slice(0, start - 2);
      const after = input.value.slice(start);
      const raw = (before + after).replace(/[^\d]/g, '');

      if (raw === '') {
        setDisplayValue('');
        const syntheticEvent = {
          target: { name, value: '', type: 'text' },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        onChange(syntheticEvent);
        return;
      }

      const num = parseInt(raw, 10);
      const formatted = formatNumberCOP(num);
      setDisplayValue(formatted);

      const syntheticEvent = {
        target: { name, value: num.toString(), type: 'number' },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      onChange(syntheticEvent);

      const digitsBefore = before.replace(/[^\d]/g, '').length;
      let newPos = 0;
      let dCount = 0;
      for (let i = 0; i < formatted.length; i++) {
        if (/\d/.test(formatted[i])) dCount++;
        if (dCount === digitsBefore) {
          newPos = i + 1;
          break;
        }
      }
      if (digitsBefore === 0) newPos = 0;

      requestAnimationFrame(() => {
        if (inputRef.current) {
          inputRef.current.setSelectionRange(newPos, newPos);
        }
      });
      return;
    }

    // Caso 2: Delete (suprimir) cuando el caracter a la derecha es un punto de miles
    if (e.key === 'Delete' && start < input.value.length && input.value[start] === '.') {
      e.preventDefault();
      // Eliminar el digito posterior al punto (start + 1)
      const before = input.value.slice(0, start);
      const after = input.value.slice(start + 2);
      const raw = (before + after).replace(/[^\d]/g, '');

      if (raw === '') {
        setDisplayValue('');
        const syntheticEvent = {
          target: { name, value: '', type: 'text' },
        } as unknown as React.ChangeEvent<HTMLInputElement>;
        onChange(syntheticEvent);
        return;
      }

      const num = parseInt(raw, 10);
      const formatted = formatNumberCOP(num);
      setDisplayValue(formatted);

      const syntheticEvent = {
        target: { name, value: num.toString(), type: 'number' },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      onChange(syntheticEvent);

      const digitsBefore = before.replace(/[^\d]/g, '').length;
      let newPos = 0;
      let dCount = 0;
      for (let i = 0; i < formatted.length; i++) {
        if (/\d/.test(formatted[i])) dCount++;
        if (dCount === digitsBefore) {
          newPos = i + 1;
          break;
        }
      }
      if (digitsBefore === 0) newPos = 0;

      requestAnimationFrame(() => {
        if (inputRef.current) {
          inputRef.current.setSelectionRange(newPos, newPos);
        }
      });
    }
  };

  return (
    <input
      ref={inputRef}
      type="text"
      inputMode="numeric"
      id={id || name}
      name={name}
      value={displayValue}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      className={className}
      disabled={disabled}
      required={required}
      autoComplete="off"
    />
  );
};
