/**
 * UI-01.006 - Gavetas inteligentes da Sidebar
 *
 * A estrutura Django original nao e alterada.
 * As gavetas sao criadas apenas no DOM ja renderizado,
 * depois que permissoes e condicionais foram processadas.
 */
(function () {
    "use strict";

    const STORAGE_KEY = "cashback.sidebar.drawer.open";
    const SECTION_LABELS = new Map([
        ["operação", "operacao"],
        ["operacao", "operacao"],
        ["pdv", "pdv"],
        ["compras", "compras"],
        ["importações", "importacoes"],
        ["importacoes", "importacoes"],
        ["minha empresa", "minha-empresa"],
        ["gestão", "minha-empresa"],
        ["gestao", "minha-empresa"],
        ["empresa", "minha-empresa"],
        ["recursos humanos", "rh"],
        ["rh", "rh"],
        ["campanhas", "campanhas"]
    ]);

    function normalizeText(value) {
        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim()
            .toLowerCase();
    }

    function getSectionKey(element) {
        if (!element || element.matches("a, button")) {
            return null;
        }

        const normalized = normalizeText(element.textContent);

        for (const [label, key] of SECTION_LABELS.entries()) {
            if (normalizeText(label) === normalized) {
                return key;
            }
        }

        return null;
    }

    function findSidebarNav() {
        const navs = Array.from(document.querySelectorAll("aside.bg-dark nav"));

        return navs.find(function (nav) {
            return nav.querySelectorAll(".nav-link").length >= 2;
        }) || null;
    }

    function createTrigger(originalHeading, sectionKey, contentId) {
        const trigger = document.createElement("button");
        const label = originalHeading.textContent.trim();

        trigger.type = "button";
        trigger.className = "sidebar-drawer__trigger";
        trigger.dataset.sidebarDrawerTrigger = sectionKey;
        trigger.setAttribute("aria-controls", contentId);
        trigger.setAttribute("aria-expanded", "false");

        const labelElement = document.createElement("span");
        labelElement.className = "sidebar-drawer__label";
        labelElement.textContent = label;

        const chevron = document.createElement("i");
        chevron.className = "bi bi-chevron-down sidebar-drawer__chevron";
        chevron.setAttribute("aria-hidden", "true");

        trigger.appendChild(labelElement);
        trigger.appendChild(chevron);

        const originalClassName = originalHeading.className || "";

        if (originalClassName.includes("mt-4")) {
            trigger.classList.add("sidebar-drawer__trigger--spaced");
        }

        return trigger;
    }

    function setDrawerState(drawer, isOpen, animate) {
        const trigger = drawer.querySelector(":scope > .sidebar-drawer__trigger");
        const content = drawer.querySelector(":scope > .sidebar-drawer__content");

        if (!trigger || !content) {
            return;
        }

        drawer.classList.toggle("is-open", isOpen);
        trigger.setAttribute("aria-expanded", String(isOpen));

        if (!animate) {
            content.classList.add("sidebar-drawer__content--no-transition");
        }

        if (isOpen) {
            content.hidden = false;

            window.requestAnimationFrame(function () {
                content.style.maxHeight = content.scrollHeight + "px";
                content.style.opacity = "1";
            });
        }
        else {
            content.style.maxHeight = "0px";
            content.style.opacity = "0";

            window.setTimeout(function () {
                if (!drawer.classList.contains("is-open")) {
                    content.hidden = true;
                }
            }, animate ? 220 : 0);
        }

        if (!animate) {
            window.requestAnimationFrame(function () {
                content.classList.remove("sidebar-drawer__content--no-transition");
            });
        }
    }

    function closeOtherDrawers(drawers, currentDrawer) {
        drawers.forEach(function (drawer) {
            if (drawer !== currentDrawer) {
                setDrawerState(drawer, false, true);
            }
        });
    }

    function getActiveDrawer(drawers) {
        return drawers.find(function (drawer) {
            return Boolean(
                drawer.querySelector(".sidebar-drawer__content .nav-link.active")
            );
        }) || null;
    }

    function getStoredDrawer(drawers) {
        try {
            const storedKey = window.sessionStorage.getItem(STORAGE_KEY);

            return drawers.find(function (drawer) {
                return drawer.dataset.sidebarDrawer === storedKey;
            }) || null;
        }
        catch (error) {
            return null;
        }
    }

    function storeDrawer(sectionKey) {
        try {
            if (sectionKey) {
                window.sessionStorage.setItem(STORAGE_KEY, sectionKey);
            }
            else {
                window.sessionStorage.removeItem(STORAGE_KEY);
            }
        }
        catch (error) {
            // O menu continua funcional mesmo sem armazenamento.
        }
    }

    function buildDrawers(nav) {
        const directChildren = Array.from(nav.children);
        const headings = directChildren
            .map(function (element, index) {
                return {
                    element: element,
                    index: index,
                    key: getSectionKey(element)
                };
            })
            .filter(function (item) {
                return Boolean(item.key);
            });

        if (headings.length < 2) {
            return [];
        }

        const drawers = [];

        headings.forEach(function (heading, headingIndex) {
            const nextHeading = headings[headingIndex + 1];
            const endIndex = nextHeading ? nextHeading.index : directChildren.length;
            const sectionElements = directChildren.slice(
                heading.index + 1,
                endIndex
            );

            if (sectionElements.length === 0) {
                return;
            }

            const drawer = document.createElement("section");
            const content = document.createElement("div");
            const contentId = "sidebar-drawer-content-" + heading.key;
            const trigger = createTrigger(
                heading.element,
                heading.key,
                contentId
            );

            drawer.className = "sidebar-drawer";
            drawer.dataset.sidebarDrawer = heading.key;

            content.id = contentId;
            content.className = "sidebar-drawer__content";
            content.dataset.sidebarDrawerContent = heading.key;
            content.hidden = true;
            content.style.maxHeight = "0px";
            content.style.opacity = "0";

            heading.element.parentNode.insertBefore(drawer, heading.element);
            drawer.appendChild(trigger);
            drawer.appendChild(content);

            sectionElements.forEach(function (element) {
                content.appendChild(element);
            });

            heading.element.remove();

            drawers.push(drawer);
        });

        return drawers;
    }

    function initializeSidebarDrawers() {
        const nav = findSidebarNav();

        if (!nav || nav.dataset.sidebarDrawersReady === "true") {
            return;
        }

        const drawers = buildDrawers(nav);

        if (drawers.length === 0) {
            return;
        }

        nav.dataset.sidebarDrawersReady = "true";

        drawers.forEach(function (drawer) {
            const trigger = drawer.querySelector(
                ":scope > .sidebar-drawer__trigger"
            );

            trigger.addEventListener("click", function () {
                const willOpen = !drawer.classList.contains("is-open");

                closeOtherDrawers(drawers, drawer);
                setDrawerState(drawer, willOpen, true);
                storeDrawer(willOpen ? drawer.dataset.sidebarDrawer : null);
            });

            trigger.addEventListener("keydown", function (event) {
                if (event.key !== "ArrowDown" && event.key !== "ArrowUp") {
                    return;
                }

                event.preventDefault();

                const currentIndex = drawers.indexOf(drawer);
                const direction = event.key === "ArrowDown" ? 1 : -1;
                const targetIndex = (
                    currentIndex + direction + drawers.length
                ) % drawers.length;

                const targetTrigger = drawers[targetIndex].querySelector(
                    ":scope > .sidebar-drawer__trigger"
                );

                targetTrigger.focus();
            });
        });

        const activeDrawer = getActiveDrawer(drawers);
        const storedDrawer = getStoredDrawer(drawers);
        const initialDrawer = activeDrawer || storedDrawer || drawers[0];

        drawers.forEach(function (drawer) {
            setDrawerState(drawer, drawer === initialDrawer, false);
        });

        storeDrawer(initialDrawer.dataset.sidebarDrawer);

        window.addEventListener("resize", function () {
            const openDrawer = drawers.find(function (drawer) {
                return drawer.classList.contains("is-open");
            });

            if (!openDrawer) {
                return;
            }

            const content = openDrawer.querySelector(
                ":scope > .sidebar-drawer__content"
            );

            content.style.maxHeight = content.scrollHeight + "px";
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeSidebarDrawers,
            { once: true }
        );
    }
    else {
        initializeSidebarDrawers();
    }
})();