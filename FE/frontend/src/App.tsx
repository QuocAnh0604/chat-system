import { BrowserRouter, Routes, Route } from "react-router-dom";

import LandingPage from "./PAGES/LandingPage";
import LoginPage from "./PAGES/LoginPage";
import RegisterPage from "./PAGES/RegisterPage";
import ChatHomePage from "./PAGES/ChatHomePage";
import ProfilePage from "./PAGES/ProfilePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage/>}/>
        <Route path="/chat" element={<ChatHomePage/>}/>
         <Route path="/profile" element={<ProfilePage/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;