import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import IPhone13141 from './pages/IPhone13141';
function App() {
  return (
    <BrowserRouter>
        <Routes>
			<Route path="/" element={<IPhone13141 />} />
			<Route path="/IPhone13141" element={<IPhone13141 />} />
        </Routes>
    </BrowserRouter>
  );
}
export default App;