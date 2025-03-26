import reactPlugin from "eslint-plugin-react"
import hooksPlugin from "eslint-plugin-react-hooks"
import tseslint from "typescript-eslint"

/**
 * ESLint configuration for React authentik projects.
 */
export const reactConfig = tseslint.config(
	{
		settings: {
			react: {
				version: "detect",
			},
		},

		plugins: {
			// @ts-ignore Fixup plugin rules.
			react: reactPlugin,
			// @ts-ignore Fixup plugin
			"react-hooks": hooksPlugin,
		},

		rules: {
			"react-hooks/rules-of-hooks": "error",
			"react-hooks/exhaustive-deps": "warn",

			"react/jsx-uses-react": 0,

			"react/display-name": "off",
			"react/jsx-curly-brace-presence": "error",
			"react/jsx-no-leaked-render": "error",
			"react/prop-types": "off",
			"react/react-in-jsx-scope": "off",
		},
	}
)

export default reactConfig
