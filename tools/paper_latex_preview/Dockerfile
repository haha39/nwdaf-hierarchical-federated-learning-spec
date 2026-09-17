FROM texlive/texlive@sha256:5c7cd9ddeab249eaa28e2b5d4c4c9a9de49c0c37815493965b2b54401b73f07f

# Validated package set for the local ACM sigconf preview; avoid broad collections.
RUN tlmgr --repository https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet install \
    acmart booktabs caption cmap comment environ everyshi float fontaxes framed \
    hyperxmp inconsolata kastrup libertine microtype mweights ncctools newtx \
    pbalance preprint setspace totpages trimspaces upquote xcolor xkeyval \
    xstring zref
