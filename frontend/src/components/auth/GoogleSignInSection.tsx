import { GoogleLogin } from "@react-oauth/google";

type Mode = "login" | "register";

interface Props {
  mode: Mode;
  onSuccess: (credential?: string) => void;
  disabled?: boolean;
}

/** Only rendered when VITE_GOOGLE_CLIENT_ID is set (see main.tsx). */
export function GoogleSignInSection({ mode, onSuccess }: Props) {
  return (
    <div className="mb-6 space-y-4">
      <div className="flex justify-center [&>div]:w-full">
        <GoogleLogin
          onSuccess={(res) => onSuccess(res.credential)}
          onError={() => onSuccess(undefined)}
          theme="outline"
          size="large"
          width="360"
          text={mode === "login" ? "signin_with" : "signup_with"}
          shape="rectangular"
          useOneTap={false}
        />
      </div>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white/80 px-3 text-ink-400">or continue with email</span>
        </div>
      </div>
    </div>
  );
}
