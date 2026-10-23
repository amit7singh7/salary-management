// React + htm come from CDN <script> tags (see index.html); re-exported here for modules.
export const { useState, useEffect, useRef, useCallback, useMemo } = React;
export const html = htm.bind(React.createElement);
