import { auth, signIn, signOut } from "@/auth"
import ChatInterface from "./components/ChatInterface"

export default async function Home() {
  const session = await auth()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-blue-900">Socratic Tutor Pro</h1>
        {session && (
          <p className="text-sm text-gray-500 mt-2">
            Ready to learn, <span className="font-semibold text-blue-600">{session.user?.email}</span>?
          </p>
        )}
      </header>
      
      {session ? (
        <div className="w-full max-w-2xl flex flex-col items-center">
          {/* This is the component that talks to your FastAPI backend */}
          <ChatInterface userId={session.user?.email || "anonymous"} />

          <form action={async () => { "use server"; await signOut(); }} className="mt-12">
            <button className="text-gray-400 hover:text-red-500 text-xs transition-colors underline">
              Sign Out
            </button>
          </form>
        </div>
      ) : (
        <div className="bg-white p-10 rounded-2xl shadow-xl text-center border border-gray-100">
          <p className="mb-6 text-gray-600 text-lg">Your personal AI tutor for deep understanding.</p>
          <form action={async () => { "use server"; await signIn("google"); }}>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-bold shadow-lg transition-transform active:scale-95">
              Sign in with Google
            </button>
          </form>
        </div>
      )}
    </main>
  )
}