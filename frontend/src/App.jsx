import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import MapPage from './pages/MapPage'
import DatabasesPage from './pages/DatabasesPage'
import ParkingPage from './pages/parking/ParkingPage'
import ChargersPage from './pages/parking/ChargersPage'
import CommitteesPage from './pages/CommitteesPage'
import EnergyCompaniesPage from './pages/EnergyCompaniesPage'
import ParkingDevicesPage from './pages/ParkingDevicesPage'
import PlansPage from './pages/PlansPage'

function App() {
  return (
    <BrowserRouter>
      <div className="w-full h-full">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/databases" element={<DatabasesPage />} />
          <Route path="/parking" element={<ParkingPage />} />
          <Route path="/chargers" element={<ChargersPage />} />
          <Route path="/committees" element={<CommitteesPage />} />
          <Route path="/energy-companies" element={<EnergyCompaniesPage />} />
          <Route path="/parking-devices" element={<ParkingDevicesPage />} />
          <Route path="/plans" element={<PlansPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
