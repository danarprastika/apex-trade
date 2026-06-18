import { Navigate, Route, Routes } from 'react-router-dom'
import AuthGuard from '../components/AuthGuard'
import RoleGuard from '../components/guards/RoleGuard'
import Layout from '../components/Layout'
import JournalPage from '../features/journal/JournalPage'
import AdminPage from '../pages/AdminPage'
import DashboardPage from '../pages/DashboardPage'
import LoginPage from '../pages/LoginPage'
import MarketPage from '../pages/MarketPage'
import NewsPage from '../pages/NewsPage'
import PortfolioPage from '../pages/PortfolioPage'
import SettingsPage from '../pages/SettingsPage'
import TradingPage from '../pages/TradingPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
        <Route index element={<DashboardPage />} />
        <Route path="market" element={<MarketPage />} />
        <Route path="trading" element={<TradingPage />} />
        <Route path="journal" element={<JournalPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="news" element={<NewsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="admin" element={
          <RoleGuard allowedRoles={['ADMIN', 'SUPER_ADMIN']}>
            <AdminPage />
          </RoleGuard>
        } />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
