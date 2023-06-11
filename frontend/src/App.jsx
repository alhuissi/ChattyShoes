import WebApp from "./pages/WebApp";
import { BrowserRouter, Route, Routes } from "react-router-dom"
import './App.css'
import Header from "./components/Header";

function App() {

  return (
    <main className="app transition-all ease-in">
      <Header />
        <BrowserRouter>
            <Routes>
              <Route path="/" element={<WebApp />} />
              {/*<Route path="/blog" element={<Blog blogPosts={blogPosts} />}>
                <Route path="/:id" element={<BlogPost content={getBlogContent}/>} />
              </Route>*/}
            </Routes>
        </BrowserRouter>
    </main>
  )
}

export default App
