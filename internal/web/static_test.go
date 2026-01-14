package web

import "testing"

func TestPathMatchesWithTheme(t *testing.T) {
	tests := []struct {
		name          string
		jwtPath       string
		requestedPath string
		want          bool
	}{
		{
			name:          "exact match without theme variable",
			jwtPath:       "media/public/logo.png",
			requestedPath: "media/public/logo.png",
			want:          true,
		},
		{
			name:          "no match without theme variable",
			jwtPath:       "media/public/logo.png",
			requestedPath: "media/public/other.png",
			want:          false,
		},
		{
			name:          "theme variable matches light theme",
			jwtPath:       "media/public/logo-%(theme)s.png",
			requestedPath: "media/public/logo-light.png",
			want:          true,
		},
		{
			name:          "theme variable matches dark theme",
			jwtPath:       "media/public/logo-%(theme)s.png",
			requestedPath: "media/public/logo-dark.png",
			want:          true,
		},
		{
			name:          "theme variable does not match invalid theme",
			jwtPath:       "media/public/logo-%(theme)s.png",
			requestedPath: "media/public/logo-blue.png",
			want:          false,
		},
		{
			name:          "theme variable in directory path",
			jwtPath:       "media/%(theme)s/logo.png",
			requestedPath: "media/light/logo.png",
			want:          true,
		},
		{
			name:          "multiple theme variables",
			jwtPath:       "media/%(theme)s/logo-%(theme)s.png",
			requestedPath: "media/light/logo-light.png",
			want:          true,
		},
		{
			name:          "multiple theme variables with dark",
			jwtPath:       "media/%(theme)s/logo-%(theme)s.png",
			requestedPath: "media/dark/logo-dark.png",
			want:          true,
		},
		{
			name:          "multiple theme variables mixed themes should not match",
			jwtPath:       "media/%(theme)s/logo-%(theme)s.png",
			requestedPath: "media/light/logo-dark.png",
			want:          false,
		},
		{
			name:          "theme variable with nested path",
			jwtPath:       "media/public/brand/logo-%(theme)s.svg",
			requestedPath: "media/public/brand/logo-dark.svg",
			want:          true,
		},
		{
			name:          "empty paths",
			jwtPath:       "",
			requestedPath: "",
			want:          true,
		},
		{
			name:          "theme variable only",
			jwtPath:       "%(theme)s",
			requestedPath: "light",
			want:          true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := pathMatchesWithTheme(tt.jwtPath, tt.requestedPath)
			if got != tt.want {
				t.Errorf("pathMatchesWithTheme(%q, %q) = %v, want %v",
					tt.jwtPath, tt.requestedPath, got, tt.want)
			}
		})
	}
}
