import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { FileUpload } from './components/FileUpload';
import { FlashcardList } from './components/FlashcardList';
import { Flashcard } from './types';
import { Toaster } from 'react-hot-toast';

function MainContent() {
  const { user } = useAuth();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [showRegister, setShowRegister] = useState(false);

  if (!user.isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        {showRegister ? (
          <Register onSwitchToLogin={() => setShowRegister(false)} />
        ) : (
          <Login onSwitchToRegister={() => setShowRegister(true)} />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <FileUpload onFlashcardsReceived={setFlashcards} />
      {flashcards.length > 0 && <FlashcardList flashcards={flashcards} />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <MainContent />
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default App;