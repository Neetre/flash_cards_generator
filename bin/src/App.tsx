import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './components/Login';
import { FileUpload } from './components/FileUpload';
import { FlashcardList } from './components/FlashcardList';
import { Flashcard } from './types';
import { Toaster } from 'react-hot-toast';

function MainContent() {
  const { user } = useAuth();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);

  if (!user.isAuthenticated) {
    return <Login />;
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