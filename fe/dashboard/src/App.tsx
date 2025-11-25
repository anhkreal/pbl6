import { BrowserRouter } from 'react-router-dom';
// ...existing imports...

function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      {/* ...existing routes... */}
    </BrowserRouter>
  );
}

export default App;
