import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import zh from './locales/zh.json'
import en from './locales/en.json'
import de from './locales/de.json'

i18n.use(initReactI18next).init({
  resources: {
    zh: { translation: zh },
    en: { translation: en },
    de: { translation: de },
  },
  lng: localStorage.getItem('language') ?? 'zh',
  fallbackLng: 'zh',
  interpolation: { escapeValue: false },
})

export default i18n
